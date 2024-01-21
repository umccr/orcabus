use async_trait::async_trait;
use chrono::{DateTime, Utc};
use sqlx::query_file;
use tracing::trace;

use crate::database::{Client, Ingest};
use crate::error::Result;
use crate::events::aws::StorageClass;
use crate::events::aws::{Events, TransposedS3EventMessages};
use crate::events::EventSourceType;

/// An ingester for S3 events.
#[derive(Debug)]
pub struct Ingester {
    client: Client,
}

impl Ingester {
    /// Create a new ingester.
    pub fn new(client: Client) -> Self {
        Self { client }
    }

    /// Create a new ingester with a default database client.
    pub async fn with_defaults() -> Result<Self> {
        Ok(Self {
            client: Client::default().await?,
        })
    }

    /// Ingest the events into the database by calling the insert and update queries.
    pub async fn ingest_events(&self, events: Events) -> Result<()> {
        let Events {
            object_created,
            object_removed,
            ..
        } = events;

        trace!(object_created = ?object_created, "ingesting object created events");
        let TransposedS3EventMessages {
            sequencers,
            object_ids,
            event_times,
            buckets,
            keys,
            sizes,
            e_tags,
            storage_classes,
            last_modified_dates,
            ..
        } = object_created;

        query_file!(
            "../database/queries/ingester/insert_objects.sql",
            &object_ids,
            &sizes as &[Option<i64>],
            &vec![None; sizes.len()] as &[Option<String>],
        )
        .execute(&self.client.pool)
        .await?;

        query_file!(
            "../database/queries/ingester/aws/insert_s3_created_objects.sql",
            &object_ids,
            &buckets,
            &keys,
            &event_times,
            &last_modified_dates as &[Option<DateTime<Utc>>],
            &e_tags as &[Option<String>],
            &storage_classes as &[Option<StorageClass>],
            &sequencers as &[Option<String>]
        )
        .execute(&self.client.pool)
        .await?;

        trace!(object_removed = ?object_removed, "ingesting object removed events");
        let TransposedS3EventMessages {
            event_times,
            buckets,
            keys,
            ..
        } = object_removed;

        query_file!(
            "../database/queries/ingester/aws/update_deleted.sql",
            &keys,
            &buckets,
            &event_times
        )
        .execute(&self.client.pool)
        .await?;

        Ok(())
    }

    /// Get a reference to the database client.
    pub fn client(&self) -> &Client {
        &self.client
    }
}

#[async_trait]
impl Ingest for Ingester {
    async fn ingest(&self, events: EventSourceType) -> Result<()> {
        match events {
            EventSourceType::S3(events) => self.ingest_events(events).await,
        }
    }
}

#[cfg(test)]
pub(crate) mod tests {
    use crate::database::aws::ingester::Ingester;
    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::{Client, Ingest};
    use crate::events::aws::tests::{expected_events, EXPECTED_E_TAG};
    use crate::events::aws::{Events, StorageClass};
    use crate::events::EventSourceType;
    use chrono::{DateTime, Utc};
    use sqlx::postgres::PgRow;
    use sqlx::{PgPool, Row};

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_created(pool: PgPool) {
        let mut events = test_events();
        events.object_removed = Default::default();

        let ingester = test_ingester(pool);
        ingester.ingest_events(events).await.unwrap();

        let object_results = sqlx::query("select * from object")
            .fetch_one(ingester.client.pool())
            .await
            .unwrap();

        let s3_object_results = sqlx::query("select * from s3_object")
            .fetch_one(ingester.client.pool())
            .await
            .unwrap();

        assert_created(object_results, s3_object_results);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_removed(pool: PgPool) {
        let events = test_events();

        let ingester = test_ingester(pool);
        ingester.ingest_events(events).await.unwrap();

        let object_results = sqlx::query("select * from object")
            .fetch_one(ingester.client.pool())
            .await
            .unwrap();

        let s3_object_results = sqlx::query("select * from s3_object")
            .fetch_one(ingester.client.pool())
            .await
            .unwrap();

        assert_deleted(object_results, s3_object_results);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest(pool: PgPool) {
        let events = test_events();

        let ingester = test_ingester(pool);
        ingester.ingest(EventSourceType::S3(events)).await.unwrap();

        let object_results = sqlx::query("select * from object")
            .fetch_one(ingester.client.pool())
            .await
            .unwrap();
        let s3_object_results = sqlx::query("select * from s3_object")
            .fetch_one(ingester.client.pool())
            .await
            .unwrap();

        assert_deleted(object_results, s3_object_results);
    }

    pub(crate) fn assert_created(object_results: PgRow, s3_object_results: PgRow) {
        assert_eq!("bucket", s3_object_results.get::<String, _>("bucket"));
        assert_eq!("key", s3_object_results.get::<String, _>("key"));
        assert_eq!(0, object_results.get::<i32, _>("size"));
        assert_eq!(EXPECTED_E_TAG, s3_object_results.get::<String, _>("e_tag"));
        assert_eq!(
            DateTime::<Utc>::default(),
            s3_object_results.get::<DateTime<Utc>, _>("created_date")
        );
        assert_eq!(
            DateTime::<Utc>::default(),
            s3_object_results.get::<DateTime<Utc>, _>("last_modified_date")
        );
    }

    pub(crate) fn assert_deleted(object_results: PgRow, s3_object_results: PgRow) {
        assert_eq!("bucket", s3_object_results.get::<String, _>("bucket"));
        assert_eq!("key", s3_object_results.get::<String, _>("key"));
        assert_eq!(0, object_results.get::<i32, _>("size"));
        assert_eq!(EXPECTED_E_TAG, s3_object_results.get::<String, _>("e_tag"));
        assert_eq!(
            DateTime::<Utc>::default(),
            s3_object_results.get::<DateTime<Utc>, _>("created_date")
        );
        assert_eq!(
            DateTime::<Utc>::default(),
            s3_object_results.get::<DateTime<Utc>, _>("last_modified_date")
        );
        assert_eq!(
            DateTime::<Utc>::default(),
            s3_object_results.get::<DateTime<Utc>, _>("deleted_date")
        );
    }

    fn test_events() -> Events {
        let mut events = expected_events();

        events.object_created.last_modified_dates[0] = Some(DateTime::default());
        events.object_created.storage_classes[0] = Some(StorageClass::Standard);

        events.object_removed.last_modified_dates[0] = Some(DateTime::default());
        events.object_removed.storage_classes[0] = None;

        events
    }
    fn test_ingester(pool: PgPool) -> Ingester {
        Ingester::new(Client::new(pool))
    }
}
