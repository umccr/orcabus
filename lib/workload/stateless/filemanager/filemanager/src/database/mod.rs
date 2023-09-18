use sqlx::PgPool;

use crate::error::Error::DbClientError;
use crate::error::Result;

pub mod s3;

#[derive(Debug)]
pub struct DbClient {
    pool: PgPool,
}

impl DbClient {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    pub async fn new_with_defaults() -> Result<Self> {
        let url = std::env::var("DATABASE_URL").map_err(|err| DbClientError(err.to_string()))?;

        Ok(Self {
            pool: PgPool::connect(&url).await?,
        })
    }

    pub fn pool(&self) -> &PgPool {
        &self.pool
    }
}
