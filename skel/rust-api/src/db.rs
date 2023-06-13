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

pub async fn query() -> sqlx::mysql::MySqlRow {
    let pool = MySqlPool::connect("mysql://orcabus:orcabus@localhost/orcabus").await;
    let res = sqlx::query("SELECT path FROM orcabus.data_portal_gdsfile")
        .fetch_one(&pool.unwrap())
        .await;

    dbg!(&res);
    res.unwrap()
}

// #[tokio::main]
// async fn main() {
//     query();
// }