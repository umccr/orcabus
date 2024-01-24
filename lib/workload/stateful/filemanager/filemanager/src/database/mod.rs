//! This module handles connecting to the filemanager database for actions such as ingesting events.
//!

use crate::env::read_env;
use async_trait::async_trait;
use sqlx::PgPool;

use crate::error::Result;
use crate::events::EventSourceType;

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
    async fn ingest(&self, events: EventSourceType) -> Result<()>;
}

/// Trait representing database migrations.
#[async_trait]
pub trait Migrate {
    /// Migrate the database.
    async fn migrate(&self) -> Result<()>;
}

#[cfg(test)]
pub(crate) mod tests {
    use crate::database::aws::ingester::tests::{test_events, test_ingester};
    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::events::aws::tests::{EXPECTED_NEW_SEQUENCER_ONE, EXPECTED_VERSION_ID};
    use crate::events::aws::Events;
    use sqlx::{query_file, PgPool};

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn select_reordered_for_deleted_event_created(pool: PgPool) {
        let mut events = test_events();
        events.object_removed = Default::default();

        test_select_reordered_for_deleted(pool, test_events()).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn select_reordered_for_deleted_event_deleted(pool: PgPool) {
        test_select_reordered_for_deleted(pool, test_events()).await;
    }

    async fn test_select_reordered_for_deleted(pool: PgPool, events: Events) {
        let ingester = test_ingester(pool);
        ingester.ingest_events(events.clone()).await.unwrap();

        let sequencers = query_file!(
            "../database/queries/ingester/aws/select_reordered_for_deleted.sql",
            "bucket",
            "key",
            EXPECTED_VERSION_ID,
            EXPECTED_NEW_SEQUENCER_ONE
        )
        .fetch_all(ingester.client().pool())
        .await
        .unwrap();

        assert_eq!(sequencers.len(), 1);
        assert_eq!(
            sequencers[0].object_id,
            Some(events.object_created.object_ids[0])
        );
    }
}
