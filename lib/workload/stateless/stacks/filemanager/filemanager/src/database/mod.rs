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
use crate::database::entities::sea_orm_active_enums::Reason;
use crate::env::Config;
use crate::error::Result;
use crate::events::aws::{FlatS3EventMessage, FlatS3EventMessages};
use crate::events::EventSourceType;

pub mod aws;
pub mod entities;

/// A trait which can generate database credentials.
#[async_trait]
pub trait CredentialGenerator {
    /// Generate the password used to connect to the database.
    async fn generate_password(&self) -> Result<String>;
}

/// A database client handles database interaction.
#[derive(Debug, Clone)]
pub struct Client {
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
            EventSourceType::S3Paired(mut events) => {
                // Disallow restores and storage class change for paired ingester because
                // the null sequencer values are not properly supported.
                let filter_reason = |event: &FlatS3EventMessage| {
                    !matches!(
                        event.reason,
                        Reason::Restored | Reason::StorageClassChanged | Reason::RestoreExpired
                    )
                };

                let created: FlatS3EventMessages = events.object_created.clone().into();
                events.object_created = FlatS3EventMessages(
                    created
                        .0
                        .into_iter()
                        .filter(filter_reason)
                        .collect::<Vec<_>>(),
                )
                .into();
                let deleted: FlatS3EventMessages = events.object_deleted.clone().into();
                events.object_deleted = FlatS3EventMessages(
                    deleted
                        .0
                        .into_iter()
                        .filter(filter_reason)
                        .collect::<Vec<_>>(),
                )
                .into();

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
    use sea_orm::prelude::Json;
    use sqlx::{query, Executor, PgPool, Row};

    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::entities::sea_orm_active_enums::{ArchiveStatus, Reason};
    use crate::events::aws::message::EventType;
    use crate::events::aws::message::EventType::{Created, Deleted};
    use crate::events::aws::tests::{EXPECTED_SEQUENCER_CREATED_ONE, EXPECTED_VERSION_ID};
    use crate::events::aws::StorageClass;
    use crate::uuid::UuidGenerator;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn insert_created(pool: PgPool) {
        insert_s3_objects(&pool, Created, Some(StorageClass::Standard), None).await;

        let inserted = query(
            "select s3_object_id as \"s3_object_id!\",
                bucket,
                key,
                event_time,
                last_modified_date,
                e_tag,
                storage_class as \"storage_class: StorageClass\",
                version_id,
                sequencer,
                is_accessible,
                number_duplicate_events from s3_object order by sequencer",
        )
        .fetch_all(&pool)
        .await
        .unwrap();

        assert_eq!(inserted.len(), 1);
        assert_eq!(
            inserted[0].get::<Option<String>, _>("sequencer"),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string())
        );
        assert_eq!(
            inserted[0].get::<Option<DateTime<Utc>>, _>("event_time"),
            Some(DateTime::default())
        );
        assert!(inserted[0].get::<bool, _>("is_accessible"),);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn insert_deleted(pool: PgPool) {
        insert_s3_objects(&pool, Deleted, Some(StorageClass::Standard), None).await;

        let inserted = query(
            "select s3_object_id as \"s3_object_id!\",
                bucket,
                key,
                event_time,
                last_modified_date,
                e_tag,
                storage_class as \"storage_class: StorageClass\",
                version_id,
                sequencer,
                is_accessible,
                number_duplicate_events from s3_object order by sequencer",
        )
        .fetch_all(&pool)
        .await
        .unwrap();

        assert_eq!(inserted.len(), 1);
        assert_eq!(
            inserted[0].get::<Option<String>, _>("sequencer"),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string())
        );
        assert_eq!(
            inserted[0].get::<Option<DateTime<Utc>>, _>("event_time"),
            Some(DateTime::default())
        );
        assert!(!inserted[0].get::<bool, _>("is_accessible"),);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_is_accessible(pool: PgPool) {
        assert_is_accessible(
            &pool,
            Created,
            Some(StorageClass::GlacierIr),
            Some(ArchiveStatus::DeepArchiveAccess),
            true,
        )
        .await;
        assert_is_accessible(
            &pool,
            Created,
            Some(StorageClass::Standard),
            Some(ArchiveStatus::ArchiveAccess),
            true,
        )
        .await;
        assert_is_accessible(&pool, Created, Some(StorageClass::StandardIa), None, true).await;

        assert_is_accessible(
            &pool,
            Created,
            Some(StorageClass::IntelligentTiering),
            None,
            true,
        )
        .await;

        assert_is_accessible(&pool, Deleted, Some(StorageClass::Standard), None, false).await;
        assert_is_accessible(
            &pool,
            Created,
            Some(StorageClass::IntelligentTiering),
            Some(ArchiveStatus::DeepArchiveAccess),
            false,
        )
        .await;
        assert_is_accessible(
            &pool,
            Created,
            Some(StorageClass::IntelligentTiering),
            Some(ArchiveStatus::ArchiveAccess),
            false,
        )
        .await;

        assert_is_accessible(
            &pool,
            Created,
            Some(StorageClass::Glacier),
            Some(ArchiveStatus::DeepArchiveAccess),
            false,
        )
        .await;
        assert_is_accessible(&pool, Created, Some(StorageClass::Glacier), None, false).await;
        assert_is_accessible(&pool, Created, Some(StorageClass::DeepArchive), None, false).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn insert_s3_crawl(pool: PgPool) {
        let insert_query = |bucket, prefix, status| {
            format!(
                "insert into s3_crawl (s3_crawl_id, status, bucket, prefix) values (
                    '{}',
                    '{}',
                    '{}',
                    '{}'
                )",
                UuidGenerator::generate(),
                status,
                bucket,
                prefix
            )
        };

        // InProgress inserts on different buckets are okay, or inserts with other statuses.
        query(&insert_query("bucket1", "prefix1", "InProgress"))
            .execute(&pool)
            .await
            .unwrap();
        query(&insert_query("bucket1", "prefix2", "Completed"))
            .execute(&pool)
            .await
            .unwrap();
        query(&insert_query("bucket2", "prefix1", "InProgress"))
            .execute(&pool)
            .await
            .unwrap();

        // InProgress inserts on the same bucket should be an error.
        let result = query(&insert_query("bucket1", "prefix2", "InProgress"))
            .execute(&pool)
            .await;
        assert!(result.is_err())
    }

    async fn assert_is_accessible(
        pool: &PgPool,
        event_type: EventType,
        storage_class: Option<StorageClass>,
        archive_status: Option<ArchiveStatus>,
        expected: bool,
    ) {
        insert_s3_objects(pool, event_type, storage_class, archive_status).await;

        let inserted = query(
            "select s3_object_id as \"s3_object_id!\",
                is_accessible
                from s3_object order by sequencer",
        )
        .fetch_all(pool)
        .await
        .unwrap();

        assert_eq!(inserted.len(), 1);
        assert_eq!(inserted[0].get::<bool, _>("is_accessible"), expected,);

        pool.execute("truncate s3_object").await.unwrap();
    }

    async fn insert_s3_objects(
        pool: &PgPool,
        event_type: EventType,
        storage_class: Option<StorageClass>,
        archive_status: Option<ArchiveStatus>,
    ) {
        query(include_str!(
            "../../../database/queries/ingester/aws/insert_s3_objects.sql"
        ))
        .bind(vec![UuidGenerator::generate()])
        .bind(vec!["bucket".to_string()])
        .bind(vec!["key".to_string()])
        .bind(vec![DateTime::<Utc>::default()])
        .bind(vec![Some(0i64)])
        .bind(vec![None::<String>])
        .bind(vec![DateTime::<Utc>::default()])
        .bind(vec![None::<String>])
        .bind(vec![storage_class])
        .bind(vec![EXPECTED_VERSION_ID.to_string()])
        .bind(vec![EXPECTED_SEQUENCER_CREATED_ONE.to_string()])
        .bind(vec![false])
        .bind(vec![Reason::Unknown])
        .bind(vec![archive_status])
        .bind(vec![event_type.clone()])
        .bind(vec![UuidGenerator::generate()])
        .bind(vec![matches!(event_type, Created)])
        .bind(vec![None::<Json>])
        .fetch_all(pool)
        .await
        .unwrap();
    }
}
