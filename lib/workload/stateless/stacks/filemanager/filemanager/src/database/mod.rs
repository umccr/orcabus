//! This module handles connecting to the filemanager database for actions such as ingesting events.
//!

use async_trait::async_trait;
use sqlx::postgres::PgConnectOptions;
use sqlx::PgPool;
use std::borrow::Cow;
use tracing::debug;

use crate::error::Result;
use crate::events::EventSourceType;
use crate::read_env;

pub mod aws;

/// A trait which can generate database credentials.
#[async_trait]
pub trait CredentialGenerator {
    /// Generate the password used to connect to the database.
    async fn generate_password(&self) -> Result<String>;
}

/// A database client handles database interaction.
#[derive(Debug, Clone)]
pub struct Client<'a> {
    // Use a Cow here to allow an owned pool or a shared reference to a pool.
    pool: Cow<'a, PgPool>,
}

impl<'a> Client<'a> {
    /// Create a database from an existing pool.
    pub fn new(pool: PgPool) -> Self {
        Self {
            pool: Cow::Owned(pool),
        }
    }

    /// Create a database from a reference to an existing pool.
    pub fn from_ref(pool: &'a PgPool) -> Self {
        Self {
            pool: Cow::Borrowed(pool),
        }
    }

    /// Create a database using default credential loading logic as defined in
    /// `Self::connect_options`.
    pub async fn from_generator(generator: Option<impl CredentialGenerator>) -> Result<Self> {
        Ok(Self::new(Self::create_pool(generator).await?))
    }

    /// Create a database connection pool using credential loading logic defined in
    /// `Self::connect_options`.
    pub async fn create_pool(generator: Option<impl CredentialGenerator>) -> Result<PgPool> {
        Ok(PgPool::connect_with(Self::connect_options(generator).await?).await?)
    }

    /// Create database connect options using a series of credential loading logic.
    ///
    /// First, this tries to load a DATABASE_URL environment variable to connect.
    /// Then, it uses the generator if it is not None and PGPASSWORD is not set.
    /// Otherwise, uses default logic defined in PgConnectOptions::default.
    pub async fn connect_options(
        generator: Option<impl CredentialGenerator>,
    ) -> Result<PgConnectOptions> {
        // If the DATABASE_URL is defined, use that.
        if let Ok(url) = read_env("DATABASE_URL") {
            return Ok(url.parse()?);
        }
        // If PGPASSWORD is set, use default options.
        if read_env("PGPASSWORD").is_ok() {
            return Ok(PgConnectOptions::default());
        }

        // Otherwise use generator if it is available.
        match generator {
            Some(generator) => {
                debug!("generating credentials to connect to database");
                Ok(PgConnectOptions::default().password(&generator.generate_password().await?))
            }
            None => Ok(PgConnectOptions::default()),
        }
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

    use crate::database::aws::ingester::tests::{test_events, test_ingester};
    use crate::database::aws::ingester::Ingester;
    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::events::aws::message::EventType;
    use crate::events::aws::tests::{
        EXPECTED_NEW_SEQUENCER_ONE, EXPECTED_SEQUENCER_CREATED_ONE, EXPECTED_SEQUENCER_CREATED_TWO,
        EXPECTED_SEQUENCER_CREATED_ZERO, EXPECTED_VERSION_ID,
    };
    use crate::events::aws::StorageClass;
    use crate::events::aws::{Events, FlatS3EventMessage};
    use crate::uuid::UuidGenerator;

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

        let object_id = UuidGenerator::generate();
        query_file!(
            "../database/queries/ingester/aws/insert_s3_created_objects.sql",
            &vec![UuidGenerator::generate()],
            &vec![object_id],
            &vec![UuidGenerator::generate()],
            &vec!["bucket".to_string()],
            &vec!["key".to_string()],
            &vec![DateTime::<Utc>::default()],
            &vec![Some(0i64)] as &[Option<i64>],
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

        let object_id = UuidGenerator::generate();
        query_file!(
            "../database/queries/ingester/aws/insert_s3_deleted_objects.sql",
            &vec![UuidGenerator::generate()],
            &vec![object_id],
            &vec![UuidGenerator::generate()],
            &vec!["bucket".to_string()],
            &vec!["key".to_string()],
            &vec![DateTime::<Utc>::default()],
            &vec![Some(0i64)] as &[Option<i64>],
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
            &vec![UuidGenerator::generate()],
            &vec!["bucket".to_string()],
            &vec!["key".to_string()],
            &vec![DateTime::<Utc>::default()],
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
            &vec![UuidGenerator::generate()],
            &vec!["bucket".to_string()],
            &vec!["key".to_string()],
            &vec![DateTime::<Utc>::default()],
            &vec![Some(0i64)] as &[Option<i64>],
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
