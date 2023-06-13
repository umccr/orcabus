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
    let pool = MySqlPool::connect("mysql://orcabus:orcabus@localhost/orcabus").await?;
    
    sqlx::migrate!("./migrations").run(&pool).await?;
    
    let res = sqlx::query("SELECT path FROM orcabus.data_portal_gdsfile")
        .fetch_one(&pool)
        .await?;

    dbg!(&res);
    Ok(())
}

// #[tokio::main]
// async fn main() {
//     query();
// }