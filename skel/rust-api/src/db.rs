use std::env;
use sqlx::mysql::MySqlPool;

// TODO: To be used by sqlx::query_as(), leveraging Rust's
// type system.
//
// struct GDSFile {
//     id: u64,
//     path: String,
//     // name: String,
//     // volume_id: u64,
//     // volume_name: String,
//     // size: u64
//     // time_created: chrono::DateTime<chrono::Utc>,
//     // time_archived: chrono::DateTime<chrono::Utc>,
// }

pub async fn query() -> Result<(), sqlx::Error> {
    // TODO: Move this at "class" level instead of method level
    let db_url = env::var("DATABASE_URL");
    let pool = MySqlPool::connect(db_url.unwrap_or_default().as_str()).await?;
    
    sqlx::migrate!("./migrations").run(&pool).await?;
    
    let res = sqlx::query("SELECT path FROM orcabus.data_portal_gdsfile")
        .fetch_one(&pool)
        .await?;

    dbg!(&res);
    Ok(())
}