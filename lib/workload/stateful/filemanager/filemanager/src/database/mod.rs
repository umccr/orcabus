use async_trait::async_trait;
use sqlx::PgPool;
use std::env;

use crate::error::Error::MissingDatabaseUrl;
use crate::error::Result;
use crate::events::EventType;

pub mod aws;

/// A database client handles database interaction.
#[derive(Debug)]
pub struct Client {
    pool: PgPool,
}

impl Client {
    /// Create a database from an existing pool.
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    /// Create a database with default DATABASE_URL connection.
    pub async fn default() -> Result<Self> {
        let url = env::var("DATABASE_URL").map_err(|err| MissingDatabaseUrl(err.to_string()))?;

        Ok(Self {
            pool: PgPool::connect(&url).await?,
        })
    }

    /// Get the database pool.
    pub fn pool(&self) -> &PgPool {
        &self.pool
    }
}

/// This trait ingests raw events into the database.
#[async_trait]
pub trait Ingest {
    /// Ingest the events.
    async fn ingest(&mut self, events: EventType) -> Result<()>;
}
