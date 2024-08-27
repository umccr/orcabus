//! This module handles connecting to the filemanager database for actions such as ingesting events.
//!

use async_trait::async_trait;
use sea_orm::{DatabaseConnection, SqlxPostgresConnector};
use sqlx::postgres::PgConnectOptions;
use sqlx::PgPool;
use tracing::debug;

use crate::database::aws::credentials::IamGenerator;
use crate::database::aws::ingester::Ingester;
use crate::database::aws::ingester_paired::IngesterPaired;
use crate::env::Config;
use crate::error::Result;
use crate::events::EventSourceType;

pub mod aws;

// Include the generated entities module.
include!(concat!(env!("OUT_DIR"), "/generated.rs"));

/// A trait which can generate database credentials.
#[async_trait]
pub trait CredentialGenerator {
    /// Generate the password used to connect to the database.
    async fn generate_password(&self) -> Result<String>;
}

/// A database client handles database interaction.
#[derive(Debug, Clone)]
pub struct Client {
    // Use a Cow here to allow an owned pool or a shared reference to a pool.
    connection: DatabaseConnection,
}

impl Client {
    /// Create a database from an existing pool.
    pub fn new(connection: DatabaseConnection) -> Self {
        Self { connection }
    }

    /// Create a database connection from an existing pool.
    pub fn from_pool(pool: PgPool) -> Self {
        Self::new(SqlxPostgresConnector::from_sqlx_postgres_pool(pool))
    }

    /// Create a database using default credential loading logic and without
    /// a credential generator.
    pub async fn from_config(config: &Config) -> Result<Self> {
        Self::from_generator(None::<IamGenerator>, config).await
    }

    /// Create a database using default credential loading logic as defined in
    /// `Self::connect_options`.
    pub async fn from_generator(
        generator: Option<impl CredentialGenerator>,
        config: &Config,
    ) -> Result<Self> {
        Ok(Self::from_pool(Self::create_pool(generator, config).await?))
    }

    /// Create a database connection pool using credential loading logic defined in
    /// `Self::connect_options`.
    pub async fn create_pool(
        generator: Option<impl CredentialGenerator>,
        config: &Config,
    ) -> Result<PgPool> {
        Ok(PgPool::connect_with(Self::pg_connect_options(generator, config).await?).await?)
    }

    /// Create database connect options using a series of credential loading logic.
    ///
    /// First, this tries to load a DATABASE_URL environment variable to connect.
    /// Then, it uses the generator if it is not None and PGPASSWORD is not set.
    /// Otherwise, uses default logic defined in PgConnectOptions::default.
    pub async fn pg_connect_options(
        generator: Option<impl CredentialGenerator>,
        config: &Config,
    ) -> Result<PgConnectOptions> {
        // If the DATABASE_URL is defined, use that.
        if let Some(url) = config.database_url() {
            return Ok(url.parse()?);
        }

        // If PGPASSWORD is set, use default options.
        if config.pg_password().is_some() {
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
        self.connection.get_postgres_connection_pool()
    }

    /// Get the database connection. Clones the underlying `DatabaseConnection` which is
    /// intended to be cheaply cloneable because it represents an Arc to a shared connection pool.
    pub fn connection(&self) -> DatabaseConnection {
        self.connection.clone()
    }

    /// Get the database connection as a reference.
    pub fn connection_ref(&self) -> &DatabaseConnection {
        &self.connection
    }

    /// Get the inner database connection.
    pub fn into_inner(self) -> DatabaseConnection {
        self.connection
    }
}

#[async_trait]
impl Ingest for Client {
    async fn ingest(&self, events: EventSourceType) -> Result<()> {
        match events {
            EventSourceType::S3(events) => {
                Ingester::new(Self::new(self.connection()))
                    .ingest_events(events)
                    .await
            }
            EventSourceType::S3Paired(events) => {
                IngesterPaired::new(Self::new(self.connection()))
                    .ingest_events(events)
                    .await
            }
        }
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
    use sqlx::{query, query_file, PgPool};

    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::events::aws::message::EventType;
    use crate::events::aws::message::EventType::{Created, Deleted};
    use crate::events::aws::tests::{EXPECTED_SEQUENCER_CREATED_ONE, EXPECTED_VERSION_ID};
    use crate::events::aws::StorageClass;
    use crate::uuid::UuidGenerator;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn insert_created(pool: PgPool) {
        let mut tx = pool.begin().await.unwrap();

        query_file!(
            "../database/queries/ingester/aws/insert_s3_objects.sql",
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
            &vec![false],
            &vec![Created] as &[EventType],
        )
        .fetch_all(&mut *tx)
        .await
        .unwrap();

        tx.commit().await.unwrap();

        let inserted = query!(
            "select s3_object_id as \"s3_object_id!\",
                bucket,
                key,
                event_time,
                last_modified_date,
                e_tag,
                storage_class as \"storage_class: StorageClass\",
                version_id,
                sequencer,
                number_duplicate_events from s3_object order by sequencer"
        )
        .fetch_all(&pool)
        .await
        .unwrap();

        assert_eq!(inserted.len(), 1);
        assert_eq!(
            inserted[0].sequencer,
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string())
        );
        assert_eq!(inserted[0].event_time, Some(DateTime::default()));
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn insert_deleted(pool: PgPool) {
        let mut tx = pool.begin().await.unwrap();

        query_file!(
            "../database/queries/ingester/aws/insert_s3_objects.sql",
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
            &vec![false],
            &vec![Deleted] as &[EventType],
        )
        .fetch_all(&mut *tx)
        .await
        .unwrap();

        tx.commit().await.unwrap();

        let inserted = query!(
            "select s3_object_id as \"s3_object_id!\",
                bucket,
                key,
                event_time,
                last_modified_date,
                e_tag,
                storage_class as \"storage_class: StorageClass\",
                version_id,
                sequencer,
                number_duplicate_events from s3_object order by sequencer"
        )
        .fetch_all(&pool)
        .await
        .unwrap();

        assert_eq!(inserted.len(), 1);
        assert_eq!(
            inserted[0].sequencer,
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string())
        );
        assert_eq!(inserted[0].event_time, Some(DateTime::default()));
    }
}
