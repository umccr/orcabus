//! This module handles connecting to the filemanager database for actions such as ingesting events.
//!

use crate::env::read_env;
use async_trait::async_trait;
use sqlx::PgPool;

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
        Ok(Self {
            pool: PgPool::connect(&read_env("DATABASE_URL")?).await?,
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
    async fn ingest(&self, events: EventType) -> Result<()>;
}

/// Trait representing database migrations.
#[async_trait]
pub trait Migrate {
    /// Migrate the database.
    async fn migrate(&self) -> Result<()>;
}
