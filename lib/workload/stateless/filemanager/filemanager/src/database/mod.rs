pub mod s3;

use crate::error::Error::DbClientError;
use crate::error::Result;
use aws_sdk_s3::types::StorageClass;
use chrono::{DateTime, NaiveDateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::PgPool;
use sqlx::FromRow;
use utoipa::{IntoParams, ToSchema};

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
            pool: PgPool::connect(&url).await?
        })
    }

    pub fn pool(&self) -> &PgPool {
        &self.pool
    }
}