use std::env;

use sqlx::{mysql::MySqlPool, FromRow};

// #[derive(Debug, FromRow)]
// struct GDS {
//     id: u64,
//     path: String,
//     // name: String,
//     // volume_id: u64,
//     // volume_name: String,
//     // size: u64
//     // time_created: chrono::DateTime<chrono::Utc>,
//     // time_archived: chrono::DateTime<chrono::Utc>,
// }

#[derive(Debug, FromRow)]
pub struct S3 {
    pub id: i64,
    pub bucket: String,
    pub key: String,
}

pub async fn s3_query_something() -> Result<Vec<S3>, sqlx::Error> {
    // TODO: Move this at "class" level instead of method level
    let db_url = env::var("DATABASE_URL");
    let pool = MySqlPool::connect(db_url.unwrap_or_default().as_str()).await?;

    let key = "foo";
    let objects = sqlx::query_as!(
        S3,
        "
        SELECT data_portal_s3object.id, data_portal_s3object.bucket, data_portal_s3object.key
        FROM data_portal_s3object
        WHERE data_portal_s3object.key = ?
        LIMIT 10;
        ",
        key
    )
    .fetch_all(&pool)
    .await?;

    Ok(objects)
}

pub async fn plain_query() -> Result<(), sqlx::Error> {
    // TODO: Move this at "class" level instead of method level
    let db_url = env::var("DATABASE_URL");
    let pool = MySqlPool::connect(db_url.unwrap_or_default().as_str()).await?;

    sqlx::migrate!("./migrations").run(&pool).await?;

    let res = sqlx::query("SELECT path FROM orcabus.data_portal_gdsfile LIMIT 10")
        .fetch_one(&pool)
        .await?;

    dbg!(&res);
    Ok(())
}
