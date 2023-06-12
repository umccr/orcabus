use sqlx::mysql::MySqlPool;

async fn _query() -> Result<(), sqlx::Error> {
    let pool = MySqlPool::connect("mysql://user:pass@host/database").await?;
    let _row: (i64,) = sqlx::query_as("SELECT $1")
        .bind(150_i64)
        .fetch_one(&pool)
        .await?;

    Ok(())
}

#[tokio::main]
async fn _main() {
    //query();
}
