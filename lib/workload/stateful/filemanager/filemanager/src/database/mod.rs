//! This module handles connecting to the filemanager database for actions such as ingesting events.
//!

use async_trait::async_trait;
use sqlx::PgPool;

use crate::env::read_env;
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
    use chrono::{DateTime, Utc};
    use sqlx::{query, query_file, query_file_as, PgPool};
    use uuid::Uuid;

    use crate::database::aws::ingester::tests::{test_events, test_ingester};
    use crate::database::aws::ingester::Ingester;
    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::events::aws::tests::{
        EXPECTED_NEW_SEQUENCER_ONE, EXPECTED_SEQUENCER_CREATED_ONE, EXPECTED_SEQUENCER_CREATED_TWO,
        EXPECTED_SEQUENCER_CREATED_ZERO, EXPECTED_VERSION_ID,
    };
    use crate::events::aws::EventType;
    use crate::events::aws::StorageClass;
    use crate::events::aws::{Events, FlatS3EventMessage};

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_reordered_for_deleted_event_created(pool: PgPool) {
        let mut events = test_events();
        events.object_deleted = Default::default();

        test_update_reordered_for_deleted(pool, test_events()).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_reordered_for_deleted_event(pool: PgPool) {
        test_update_reordered_for_deleted(pool, test_events()).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_reordered_for_deleted_no_update(pool: PgPool) {
        let events = test_events();
        let (_, sequencers) = ingest_events(pool, events, EXPECTED_SEQUENCER_CREATED_TWO).await;

        assert_eq!(sequencers.len(), 0);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_reordered_for_created_event_deleted(pool: PgPool) {
        let mut events = test_events();
        events.object_created = Default::default();

        test_update_reordered_for_created(pool, test_events()).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_reordered_for_created_event(pool: PgPool) {
        test_update_reordered_for_created(pool, test_events()).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_reordered_for_created_no_update(pool: PgPool) {
        let events = test_events();
        let (_, sequencers) =
            ingest_events_created(pool, events, EXPECTED_SEQUENCER_CREATED_ZERO).await;

        assert_eq!(sequencers.len(), 0);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn insert_created(pool: PgPool) {
        let mut tx = pool.begin().await.unwrap();

        let object_id = Uuid::new_v4();
        query_file!(
            "../database/queries/ingester/aws/insert_s3_created_objects.sql",
            &vec![Uuid::new_v4()],
            &vec![object_id],
            &vec!["bucket".to_string()],
            &vec!["key".to_string()],
            &vec![DateTime::<Utc>::default()],
            &vec![Some(0)] as &[Option<i32>],
            &vec![None] as &[Option<String>],
            &vec![DateTime::<Utc>::default()],
            &vec![None] as &[Option<String>],
            &vec![Some(StorageClass::Standard)] as &[Option<StorageClass>],
            &vec![EXPECTED_VERSION_ID.to_string()],
            &vec![EXPECTED_SEQUENCER_CREATED_ONE.to_string()],
        )
        .fetch_all(&mut *tx)
        .await
        .unwrap();

        query_file!(
            "../database/queries/ingester/insert_objects.sql",
            &vec![object_id],
        )
        .fetch_all(&mut *tx)
        .await
        .unwrap();

        tx.commit().await.unwrap();

        let inserted = query!(
            "select s3_object_id as \"s3_object_id!\",
                object_id as \"object_id!\",
                bucket,
                key,
                created_date,
                deleted_date,
                last_modified_date,
                e_tag,
                storage_class as \"storage_class: StorageClass\",
                version_id,
                created_sequencer,
                deleted_sequencer,
                number_reordered,
                number_duplicate_events from s3_object"
        )
        .fetch_all(&pool)
        .await
        .unwrap();

        assert_eq!(inserted.len(), 1);
        assert_eq!(inserted[0].deleted_sequencer, None);
        assert_eq!(
            inserted[0].created_sequencer,
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string())
        );
        assert_eq!(inserted[0].deleted_date, None);
        assert_eq!(inserted[0].created_date, Some(DateTime::default()));
        assert_eq!(inserted[0].number_reordered, 0);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn insert_deleted(pool: PgPool) {
        let mut tx = pool.begin().await.unwrap();

        let object_id = Uuid::new_v4();
        query_file!(
            "../database/queries/ingester/aws/insert_s3_deleted_objects.sql",
            &vec![Uuid::new_v4()],
            &vec![object_id],
            &vec!["bucket".to_string()],
            &vec!["key".to_string()],
            &vec![DateTime::<Utc>::default()],
            &vec![Some(0)] as &[Option<i32>],
            &vec![None] as &[Option<String>],
            &vec![DateTime::<Utc>::default()],
            &vec![None] as &[Option<String>],
            &vec![Some(StorageClass::Standard)] as &[Option<StorageClass>],
            &vec![EXPECTED_VERSION_ID.to_string()],
            &vec![EXPECTED_SEQUENCER_CREATED_ONE.to_string()],
            &vec![1],
        )
        .fetch_all(&mut *tx)
        .await
        .unwrap();

        query_file!(
            "../database/queries/ingester/insert_objects.sql",
            &vec![object_id],
        )
        .fetch_all(&mut *tx)
        .await
        .unwrap();

        tx.commit().await.unwrap();

        let inserted = query!(
            "select s3_object_id as \"s3_object_id!\",
                object_id as \"object_id!\",
                bucket,
                key,
                created_date,
                deleted_date,
                last_modified_date,
                e_tag,
                storage_class as \"storage_class: StorageClass\",
                version_id,
                created_sequencer,
                deleted_sequencer,
                number_reordered,
                number_duplicate_events from s3_object"
        )
        .fetch_all(&pool)
        .await
        .unwrap();

        assert_eq!(inserted.len(), 1);
        assert_eq!(inserted[0].created_sequencer, None);
        assert_eq!(
            inserted[0].deleted_sequencer,
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string())
        );
        assert_eq!(inserted[0].created_date, None);
        assert_eq!(inserted[0].deleted_date, Some(DateTime::default()));
        assert_eq!(inserted[0].number_reordered, 1);
    }

    async fn ingest_events(
        pool: PgPool,
        events: Events,
        sequencer: &str,
    ) -> (Ingester, Vec<FlatS3EventMessage>) {
        let ingester = test_ingester(pool);
        ingester.ingest_events(events).await.unwrap();

        let sequencers = query_file_as!(
            FlatS3EventMessage,
            "../database/queries/ingester/aws/update_reordered_for_deleted.sql",
            &vec![Uuid::new_v4()],
            &vec!["bucket".to_string()],
            &vec!["key".to_string()],
            &vec![DateTime::<Utc>::default()],
            &vec![Some(0)] as &[Option<i32>],
            &vec![None] as &[Option<String>],
            &vec![DateTime::<Utc>::default()],
            &vec![None] as &[Option<String>],
            &vec![Some(StorageClass::Standard)] as &[Option<StorageClass>],
            &vec![EXPECTED_VERSION_ID.to_string()],
            &vec![sequencer.to_string()],
        )
        .fetch_all(ingester.client().pool())
        .await
        .unwrap();

        (ingester, sequencers)
    }

    async fn test_update_reordered_for_deleted(pool: PgPool, events: Events) {
        let (ingester, sequencers) =
            ingest_events(pool, events.clone(), EXPECTED_NEW_SEQUENCER_ONE).await;

        assert_eq!(sequencers.len(), 1);
        assert_eq!(sequencers[0].sequencer, events.object_deleted.sequencers[0]);

        let updated = query!(
            "select s3_object_id as \"s3_object_id!\",
                object_id as \"object_id!\",
                bucket,
                key,
                created_date,
                deleted_date,
                last_modified_date,
                e_tag,
                storage_class as \"storage_class: StorageClass\",
                version_id,
                created_sequencer,
                deleted_sequencer,
                number_reordered,
                number_duplicate_events from s3_object"
        )
        .fetch_all(ingester.client().pool())
        .await
        .unwrap();

        assert_eq!(updated.len(), 1);
        assert_eq!(
            updated[0].deleted_sequencer,
            Some(EXPECTED_NEW_SEQUENCER_ONE.to_string())
        );
        assert_eq!(updated[0].deleted_date, Some(DateTime::default()));
        assert_eq!(updated[0].number_reordered, 1);
    }

    async fn ingest_events_created(
        pool: PgPool,
        events: Events,
        sequencer: &str,
    ) -> (Ingester, Vec<FlatS3EventMessage>) {
        let ingester = test_ingester(pool);
        ingester.ingest_events(events).await.unwrap();

        let sequencers = query_file_as!(
            FlatS3EventMessage,
            "../database/queries/ingester/aws/update_reordered_for_created.sql",
            &vec![Uuid::new_v4()],
            &vec!["bucket".to_string()],
            &vec!["key".to_string()],
            &vec![DateTime::<Utc>::default()],
            &vec![Some(0)] as &[Option<i32>],
            &vec![None] as &[Option<String>],
            &vec![DateTime::<Utc>::default()],
            &vec![None] as &[Option<String>],
            &vec![Some(StorageClass::Standard)] as &[Option<StorageClass>],
            &vec![EXPECTED_VERSION_ID.to_string()],
            &vec![sequencer.to_string()],
        )
        .fetch_all(ingester.client().pool())
        .await
        .unwrap();

        (ingester, sequencers)
    }

    async fn test_update_reordered_for_created(pool: PgPool, events: Events) {
        let (ingester, sequencers) =
            ingest_events_created(pool, events.clone(), EXPECTED_NEW_SEQUENCER_ONE).await;

        assert_eq!(sequencers.len(), 1);
        assert_eq!(sequencers[0].sequencer, events.object_created.sequencers[0]);

        let updated = query!(
            "select s3_object_id as \"s3_object_id!\",
                object_id as \"object_id!\",
                bucket,
                key,
                created_date,
                deleted_date,
                last_modified_date,
                e_tag,
                storage_class as \"storage_class: StorageClass\",
                version_id,
                created_sequencer,
                deleted_sequencer,
                number_reordered,
                number_duplicate_events from s3_object"
        )
        .fetch_all(ingester.client().pool())
        .await
        .unwrap();

        assert_eq!(updated.len(), 1);
        assert_eq!(
            updated[0].created_sequencer,
            Some(EXPECTED_NEW_SEQUENCER_ONE.to_string())
        );
        assert_eq!(updated[0].number_reordered, 1);
    }
}
