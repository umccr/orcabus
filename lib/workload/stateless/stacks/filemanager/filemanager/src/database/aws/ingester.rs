//! This module handles logic associated with event ingestion.
//!

use chrono::{DateTime, Utc};
use sqlx::{query_file, query_file_as};
use tracing::debug;
use uuid::Uuid;

use crate::database::{Client, CredentialGenerator};
use crate::env::Config;
use crate::error::Result;
use crate::events::aws::message::EventType;
use crate::events::aws::{StorageClass, TransposedS3EventMessages};

/// An ingester for S3 events.
#[derive(Debug)]
pub struct Ingester {
    pub(crate) client: Client,
}

/// The type representing an insert query.
#[derive(Debug)]
struct Insert {
    object_group_id: Uuid,
    number_duplicate_events: i64,
}

impl Ingester {
    /// Create a new ingester.
    pub fn new(client: Client) -> Self {
        Self { client }
    }

    /// Create a new ingester with a default database client.
    pub async fn with_defaults(
        generator: Option<impl CredentialGenerator>,
        config: &Config,
    ) -> Result<Self> {
        Ok(Self::new(Client::from_generator(generator, config).await?))
    }

    /// Reprocess inserts to find object ids that are not duplicates from the inserted events.
    fn reprocess_inserts(object_ids: Vec<Uuid>, inserted: &mut Vec<Insert>) -> Vec<Uuid> {
        object_ids
            .into_iter()
            .rev()
            .flat_map(|object_id| {
                // If we cannot find the object in our new ids, this object already exists.
                let pos = inserted.iter().rposition(|record| {
                    // This will never be `None`, maybe this is an sqlx bug?
                    record.object_group_id == object_id
                })?;

                // We can remove this to avoid searching over it again.
                let record = inserted.remove(pos);
                debug!(
                    object_id = ?record.object_group_id,
                    number_duplicate_events = record.number_duplicate_events,
                    "duplicate event found"
                );

                // This is a new event so the corresponding object should be inserted.
                Some(object_id)
            })
            .collect()
    }

    /// Ingest the events into the database by calling the insert and update queries.
    pub async fn ingest_events(&self, events: TransposedS3EventMessages) -> Result<()> {
        let mut tx = self.client().pool().begin().await?;

        debug!(
                s3_object_ids = ?events.s3_object_ids,
                "inserting events into s3_object table"
        );
        let mut inserted = query_file_as!(
            Insert,
            "../database/queries/ingester/aws/insert_s3_objects.sql",
            &events.object_group_ids,
            &events.s3_object_ids,
            &events.public_ids,
            &events.buckets,
            &events.keys,
            &events.event_times as &[Option<DateTime<Utc>>],
            &events.sizes as &[Option<i64>],
            &events.sha256s as &[Option<String>],
            &events.last_modified_dates as &[Option<DateTime<Utc>>],
            &events.e_tags as &[Option<String>],
            &events.storage_classes as &[Option<StorageClass>],
            &events.version_ids,
            &events.sequencers as &[Option<String>],
            &events.is_delete_markers as &[bool],
            &events.event_types as &[EventType],
        )
        .fetch_all(&mut *tx)
        .await?;

        let object_ids = Self::reprocess_inserts(events.object_group_ids, &mut inserted);
        // Insert only the non duplicate events.
        if !object_ids.is_empty() {
            debug!(
                object_ids = ?object_ids,
                "inserting events into object table"
            );

            query_file!(
                "../database/queries/ingester/insert_object_groups.sql",
                &object_ids,
            )
            .execute(&mut *tx)
            .await?;
        }

        tx.commit().await?;

        Ok(())
    }

    /// Get a reference to the database client.
    pub fn client(&self) -> &Client {
        &self.client
    }
}

#[cfg(test)]
pub(crate) mod tests {
    use std::ops::Add;

    use chrono::{DateTime, Utc};
    use itertools::Itertools;
    use sqlx::postgres::PgRow;
    use sqlx::{Executor, PgPool, Row};
    use tokio::time::Instant;
    use uuid::Uuid;

    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::{Client, Ingest};
    use crate::events::aws::message::EventType;
    use crate::events::aws::message::EventType::{Created, Deleted};
    use crate::events::aws::tests::{
        expected_events_simple, expected_events_simple_delete_marker, expected_flat_events_simple,
        EXPECTED_E_TAG, EXPECTED_SEQUENCER_CREATED_ONE, EXPECTED_SEQUENCER_CREATED_ZERO,
        EXPECTED_SEQUENCER_DELETED_ONE, EXPECTED_SEQUENCER_DELETED_TWO, EXPECTED_SHA256,
        EXPECTED_VERSION_ID,
    };
    use crate::events::aws::{
        FlatS3EventMessage, FlatS3EventMessages, StorageClass, TransposedS3EventMessages,
    };
    use crate::events::EventSourceType;
    use crate::events::EventSourceType::S3;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_created(pool: PgPool) {
        let events = test_events(Some(Created));

        let ingester = test_ingester(pool);
        ingester.ingest(S3(events)).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 1);
        assert_eq!(s3_object_results.len(), 1);
        assert_created(&s3_object_results[0]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_created_delete_marker(pool: PgPool) {
        let events: FlatS3EventMessages = FlatS3EventMessages::from(test_events_delete_marker())
            .0
            .into_iter()
            .filter(|event| event.event_type == Created)
            .collect();

        let ingester = test_ingester(pool);
        ingester.ingest(S3(events.into())).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 1);
        assert_eq!(s3_object_results.len(), 1);

        let message = expected_message(Some(0), EXPECTED_VERSION_ID.to_string(), true, Created);
        assert_row(
            &s3_object_results[0],
            message,
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            Some(Default::default()),
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_removed_delete_marker(pool: PgPool) {
        let events = test_events_delete_marker();

        let ingester = test_ingester(pool);
        ingester.ingest(S3(events)).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 2);
        assert_eq!(s3_object_results.len(), 2);

        let message = expected_message(Some(0), EXPECTED_VERSION_ID.to_string(), true, Created);
        assert_row(
            &s3_object_results[0],
            message,
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            Some(Default::default()),
        );

        let message = expected_message(None, EXPECTED_VERSION_ID.to_string(), false, Deleted);
        assert_row(
            &s3_object_results[1],
            message,
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            Some(Default::default()),
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_created_large_size(pool: PgPool) {
        let mut events = test_events(Some(Created));

        events
            .sizes
            .iter_mut()
            .for_each(|size| *size = Some(i64::MAX));

        let ingester = test_ingester(pool);
        ingester.ingest(S3(events)).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 1);
        assert_eq!(s3_object_results.len(), 1);
        assert_with(
            &s3_object_results[0],
            Some(i64::MAX),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Created,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_removed(pool: PgPool) {
        let events = test_events(None);

        let ingester = test_ingester(pool);
        ingester.ingest(S3(events)).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 2);
        assert_eq!(s3_object_results.len(), 2);
        assert_ingest_events(
            &s3_object_results[0],
            &s3_object_results[1],
            EXPECTED_VERSION_ID,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_duplicates(pool: PgPool) {
        let ingester = test_ingester(pool);
        ingester
            .ingest(EventSourceType::S3(test_events(None)))
            .await
            .unwrap();
        ingester
            .ingest(EventSourceType::S3(test_events(None)))
            .await
            .unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 2);
        assert_eq!(s3_object_results.len(), 2);
        assert_eq!(
            1,
            s3_object_results[0].get::<i64, _>("number_duplicate_events")
        );
        assert_eq!(
            1,
            s3_object_results[1].get::<i64, _>("number_duplicate_events")
        );
        assert_ingest_events(
            &s3_object_results[0],
            &s3_object_results[1],
            EXPECTED_VERSION_ID,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_duplicate_except_created_event_type(pool: PgPool) {
        let ingester = test_ingester(pool);
        let mut events_one = test_events(Some(Created));

        // Merge events into same ingestion.
        let flat_events: FlatS3EventMessages = replace_sequencers(
            test_events(None),
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
        )
        .into();
        flat_events
            .into_inner()
            .into_iter()
            .for_each(|event| events_one.push(event));

        ingester
            .ingest(EventSourceType::S3(events_one))
            .await
            .unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 3);
        assert_eq!(s3_object_results.len(), 3);
        assert_missing_deleted(
            &s3_object_results[0],
            &s3_object_results[1],
            EXPECTED_VERSION_ID,
        );
        assert_with(
            &s3_object_results[2],
            None,
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Deleted,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_duplicate_except_deleted_event_type(pool: PgPool) {
        let ingester = test_ingester(pool);
        let mut events_one = test_events(Some(Deleted));

        // Merge events into same ingestion.
        let flat_events: FlatS3EventMessages = replace_sequencers(
            test_events(None),
            Some(EXPECTED_SEQUENCER_DELETED_TWO.to_string()),
        )
        .into();
        flat_events
            .into_inner()
            .into_iter()
            .for_each(|event| events_one.push(event));

        ingester
            .ingest(EventSourceType::S3(events_one))
            .await
            .unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 3);
        assert_eq!(s3_object_results.len(), 3);
        assert_missing_created(
            &s3_object_results[0],
            &s3_object_results[2],
            EXPECTED_VERSION_ID,
        );
        assert_with(
            &s3_object_results[1],
            Some(0),
            Some(EXPECTED_SEQUENCER_DELETED_TWO.to_string()),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Created,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_reordered_duplicates(pool: PgPool) {
        let ingester = test_ingester(pool);
        ingester
            .ingest(EventSourceType::S3(test_events(None)))
            .await
            .unwrap();

        // No reason the order should matter if they are duplicates
        ingester
            .ingest(EventSourceType::S3(test_events(Some(Deleted))))
            .await
            .unwrap();
        ingester
            .ingest(EventSourceType::S3(test_events(Some(Created))))
            .await
            .unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 2);
        assert_eq!(s3_object_results.len(), 2);
        assert_eq!(
            1,
            s3_object_results[0].get::<i64, _>("number_duplicate_events")
        );
        assert_eq!(
            1,
            s3_object_results[1].get::<i64, _>("number_duplicate_events")
        );
        // Ordering of entries should change because of the on conflict update.
        assert_ingest_events(
            &s3_object_results[1],
            &s3_object_results[0],
            EXPECTED_VERSION_ID,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_reorder(pool: PgPool) {
        let ingester = test_ingester(pool);

        // Deleted coming before created.
        ingester
            .ingest(EventSourceType::S3(test_events(Some(Deleted))))
            .await
            .unwrap();
        ingester
            .ingest(EventSourceType::S3(test_events(Some(Created))))
            .await
            .unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 2);
        assert_eq!(s3_object_results.len(), 2);
        // Order should be different here.
        assert_ingest_events(
            &s3_object_results[1],
            &s3_object_results[0],
            EXPECTED_VERSION_ID,
        );

        let s3_object_results = fetch_results_ordered(&ingester).await;
        assert_eq!(s3_object_results.len(), 2);
        // However if querying by the sequencer, order should be correct
        assert_ingest_events(
            &s3_object_results[0],
            &s3_object_results[1],
            EXPECTED_VERSION_ID,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_reorder_different_update_field(pool: PgPool) {
        let ingester = test_ingester(pool);
        let events = test_events(None);
        // Regular ingest.
        ingester.ingest(EventSourceType::S3(events)).await.unwrap();

        let mut sequencer = EXPECTED_SEQUENCER_CREATED_ONE.to_string();
        sequencer.pop().unwrap();
        sequencer.push('5');
        let mut events =
            replace_sequencers(test_events(Some(Created)), Some(sequencer.to_string()));
        // Ingest with a different.
        events.sha256s[0] = None;
        ingester.ingest(EventSourceType::S3(events)).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 3);
        assert_eq!(s3_object_results.len(), 3);
        assert_ingest_events(
            &s3_object_results[0],
            &s3_object_results[1],
            EXPECTED_VERSION_ID,
        );

        // It's expected that a null field is present in the next event.
        let message = expected_message(Some(0), EXPECTED_VERSION_ID.to_string(), false, Created)
            .with_sha256(None);
        assert_row(
            &s3_object_results[2],
            message,
            Some(sequencer.to_string()),
            Some(Default::default()),
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_reorder_and_duplicates_complex(pool: PgPool) {
        let ingester = test_ingester(pool);
        ingester
            .ingest(EventSourceType::S3(test_events(None)))
            .await
            .unwrap();

        let event = expected_flat_events_simple().sort_and_dedup().into_inner();
        let mut event = event[0].clone();
        event.sequencer = Some(event.sequencer.unwrap().add("7"));

        let mut events = vec![event];
        events.extend(expected_flat_events_simple().sort_and_dedup().into_inner());

        let events = update_test_events(FlatS3EventMessages(events).into());
        // This also checks to make sure that the update duplicate constraint succeeds.
        ingester.ingest(EventSourceType::S3(events)).await.unwrap();

        let s3_object_results = fetch_results_ordered(&ingester).await;

        assert_eq!(s3_object_results.len(), 3);
        assert_eq!(
            1,
            s3_object_results[0].get::<i64, _>("number_duplicate_events")
        );
        assert_eq!(
            0,
            s3_object_results[1].get::<i64, _>("number_duplicate_events")
        );
        assert_eq!(
            1,
            s3_object_results[2].get::<i64, _>("number_duplicate_events")
        );

        assert_ingest_events(
            &s3_object_results[0],
            &s3_object_results[2],
            EXPECTED_VERSION_ID,
        );
        assert_with(
            &s3_object_results[1],
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string().add("7")),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Created,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_without_version_id(pool: PgPool) {
        let ingester = test_ingester(pool);
        let events = remove_version_ids(test_events(None));

        ingester.ingest(EventSourceType::S3(events)).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 2);
        assert_eq!(s3_object_results.len(), 2);
        assert_ingest_events(
            &s3_object_results[0],
            &s3_object_results[1],
            &FlatS3EventMessage::default_version_id(),
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_duplicates_without_version_id(pool: PgPool) {
        let ingester = test_ingester(pool);
        ingester
            .ingest(EventSourceType::S3(remove_version_ids(test_events(None))))
            .await
            .unwrap();
        ingester
            .ingest(EventSourceType::S3(remove_version_ids(test_events(None))))
            .await
            .unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 2);
        assert_eq!(s3_object_results.len(), 2);
        assert_eq!(
            1,
            s3_object_results[0].get::<i64, _>("number_duplicate_events")
        );
        assert_eq!(
            1,
            s3_object_results[1].get::<i64, _>("number_duplicate_events")
        );
        assert_ingest_events(
            &s3_object_results[0],
            &s3_object_results[1],
            &FlatS3EventMessage::default_version_id(),
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_reordered_duplicates_without_version_id(pool: PgPool) {
        let ingester = test_ingester(pool);
        ingester
            .ingest(EventSourceType::S3(remove_version_ids(test_events(None))))
            .await
            .unwrap();

        // No reason the order should matter if they are duplicates
        ingester
            .ingest(EventSourceType::S3(remove_version_ids(test_events(Some(
                Deleted,
            )))))
            .await
            .unwrap();
        ingester
            .ingest(EventSourceType::S3(remove_version_ids(test_events(Some(
                Created,
            )))))
            .await
            .unwrap();

        let s3_object_results = fetch_results_ordered(&ingester).await;

        assert_eq!(s3_object_results.len(), 2);
        assert_eq!(
            1,
            s3_object_results[0].get::<i64, _>("number_duplicate_events")
        );
        assert_eq!(
            1,
            s3_object_results[1].get::<i64, _>("number_duplicate_events")
        );
        assert_ingest_events(
            &s3_object_results[0],
            &s3_object_results[1],
            &FlatS3EventMessage::default_version_id(),
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_reorder_without_version_id(pool: PgPool) {
        let ingester = test_ingester(pool);

        // Deleted coming before created.
        ingester
            .ingest(EventSourceType::S3(remove_version_ids(test_events(Some(
                Deleted,
            )))))
            .await
            .unwrap();
        ingester
            .ingest(EventSourceType::S3(remove_version_ids(test_events(Some(
                Created,
            )))))
            .await
            .unwrap();

        let s3_object_results = fetch_results_ordered(&ingester).await;

        assert_eq!(s3_object_results.len(), 2);
        assert_ingest_events(
            &s3_object_results[0],
            &s3_object_results[1],
            &FlatS3EventMessage::default_version_id(),
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_duplicates_with_version_id(pool: PgPool) {
        let ingester = test_ingester(pool);
        ingester
            .ingest(EventSourceType::S3(test_events(None)))
            .await
            .unwrap();

        let event = expected_flat_events_simple().sort_and_dedup().into_inner();
        let mut event = event[0].clone();
        event.version_id = "version_id".to_string();

        let mut events = vec![event];
        events.extend(expected_flat_events_simple().sort_and_dedup().into_inner());

        let events = update_test_events(FlatS3EventMessages(events).into());

        ingester.ingest(EventSourceType::S3(events)).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 3);
        assert_eq!(s3_object_results.len(), 3);
        assert_eq!(
            0,
            s3_object_results[0].get::<i64, _>("number_duplicate_events")
        );
        assert_eq!(
            1,
            s3_object_results[1].get::<i64, _>("number_duplicate_events")
        );
        assert_eq!(
            1,
            s3_object_results[2].get::<i64, _>("number_duplicate_events")
        );

        assert_with(
            &s3_object_results[0],
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            "version_id".to_string(),
            Some(Default::default()),
            Created,
        );
        assert_ingest_events(
            &s3_object_results[1],
            &s3_object_results[2],
            EXPECTED_VERSION_ID,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_missing_deleted(pool: PgPool) {
        let ingester = test_ingester(pool);

        let events_one = test_events(Some(Created));

        // New created event with a higher sequencer.
        let events_two = replace_sequencers(
            test_events(Some(Created)),
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
        );

        ingester.ingest(S3(events_one)).await.unwrap();
        ingester.ingest(S3(events_two)).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 2);
        assert_eq!(s3_object_results.len(), 2);
        assert_missing_deleted(
            &s3_object_results[0],
            &s3_object_results[1],
            EXPECTED_VERSION_ID,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_missing_deleted_reorder(pool: PgPool) {
        let ingester = test_ingester(pool);

        let events_one = test_events(Some(Created));

        // New created event with a higher sequencer.
        let events_two = replace_sequencers(
            test_events(Some(Created)),
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
        );

        // Re-order
        ingester.ingest(S3(events_two)).await.unwrap();
        ingester.ingest(S3(events_one)).await.unwrap();

        let s3_object_results = fetch_results_ordered(&ingester).await;

        assert_eq!(s3_object_results.len(), 2);
        assert_missing_deleted(
            &s3_object_results[0],
            &s3_object_results[1],
            EXPECTED_VERSION_ID,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_missing_created(pool: PgPool) {
        let ingester = test_ingester(pool);

        let events_one = test_events(Some(Deleted));

        // New deleted event with a higher sequencer.
        let events_two = replace_sequencers(
            test_events(Some(Deleted)),
            Some(EXPECTED_SEQUENCER_DELETED_TWO.to_string()),
        );

        ingester.ingest(S3(events_one)).await.unwrap();
        ingester.ingest(S3(events_two)).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 2);
        assert_eq!(s3_object_results.len(), 2);
        assert_missing_created(
            &s3_object_results[0],
            &s3_object_results[1],
            EXPECTED_VERSION_ID,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_missing_created_reorder(pool: PgPool) {
        let ingester = test_ingester(pool);

        let events_one = test_events(Some(Deleted));

        // New deleted event with a higher sequencer.
        let events_two = replace_sequencers(
            test_events(Some(Deleted)),
            Some(EXPECTED_SEQUENCER_DELETED_TWO.to_string()),
        );

        // Re-order
        ingester.ingest(S3(events_two)).await.unwrap();
        ingester.ingest(S3(events_one)).await.unwrap();

        let s3_object_results = fetch_results_ordered(&ingester).await;

        assert_eq!(s3_object_results.len(), 2);
        assert_missing_created(
            &s3_object_results[0],
            &s3_object_results[1],
            EXPECTED_VERSION_ID,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_missing_deleted_without_version_id(pool: PgPool) {
        let ingester = test_ingester(pool);

        let events_one = remove_version_ids(test_events(Some(Created)));

        // New created event with a higher sequencer.
        let events_two = remove_version_ids(replace_sequencers(
            test_events(Some(Created)),
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
        ));

        ingester.ingest(S3(events_one)).await.unwrap();
        ingester.ingest(S3(events_two)).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 2);
        assert_eq!(s3_object_results.len(), 2);
        assert_missing_deleted(
            &s3_object_results[0],
            &s3_object_results[1],
            &FlatS3EventMessage::default_version_id(),
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_missing_deleted_reorder_without_version_id(pool: PgPool) {
        let ingester = test_ingester(pool);

        let events_one = remove_version_ids(test_events(Some(Created)));

        // New created event with a higher sequencer.
        let events_two = remove_version_ids(replace_sequencers(
            test_events(Some(Created)),
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
        ));

        ingester.ingest(S3(events_two)).await.unwrap();
        ingester.ingest(S3(events_one)).await.unwrap();

        let s3_object_results = fetch_results_ordered(&ingester).await;

        assert_eq!(s3_object_results.len(), 2);
        assert_missing_deleted(
            &s3_object_results[0],
            &s3_object_results[1],
            &FlatS3EventMessage::default_version_id(),
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_missing_created_without_version_id(pool: PgPool) {
        let ingester = test_ingester(pool);

        let events_one = remove_version_ids(test_events(Some(Deleted)));

        // New deleted event with a higher sequencer.
        let events_two = remove_version_ids(replace_sequencers(
            test_events(Some(Deleted)),
            Some(EXPECTED_SEQUENCER_DELETED_TWO.to_string()),
        ));

        ingester.ingest(S3(events_one)).await.unwrap();
        ingester.ingest(S3(events_two)).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 2);
        assert_eq!(s3_object_results.len(), 2);
        assert_missing_created(
            &s3_object_results[0],
            &s3_object_results[1],
            &FlatS3EventMessage::default_version_id(),
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_missing_created_reorder_without_version_id(pool: PgPool) {
        let ingester = test_ingester(pool);

        let events_one = remove_version_ids(test_events(Some(Deleted)));

        // New deleted event with a higher sequencer.
        let events_two = remove_version_ids(replace_sequencers(
            test_events(Some(Deleted)),
            Some(EXPECTED_SEQUENCER_DELETED_TWO.to_string()),
        ));

        ingester.ingest(S3(events_two)).await.unwrap();
        ingester.ingest(S3(events_one)).await.unwrap();

        let s3_object_results = fetch_results_ordered(&ingester).await;

        assert_eq!(s3_object_results.len(), 2);
        assert_missing_created(
            &s3_object_results[0],
            &s3_object_results[1],
            &FlatS3EventMessage::default_version_id(),
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_no_sequencer_created(pool: PgPool) {
        let ingester = test_ingester(pool);

        let events_one = replace_sequencers(test_events(Some(Created)), None);
        let events_two = replace_sequencers(test_events(Some(Created)), None);

        ingester.ingest(S3(events_one)).await.unwrap();
        ingester.ingest(S3(events_two)).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 2);
        assert_eq!(s3_object_results.len(), 2);
        assert_with(
            &s3_object_results[0],
            Some(0),
            None,
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Created,
        );
        assert_with(
            &s3_object_results[1],
            Some(0),
            None,
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Created,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_no_sequencer_deleted(pool: PgPool) {
        let ingester = test_ingester(pool);

        let events_one = replace_sequencers(test_events(Some(Deleted)), None);
        let events_two = replace_sequencers(test_events(Some(Deleted)), None);

        ingester.ingest(S3(events_one)).await.unwrap();
        ingester.ingest(S3(events_two)).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 2);
        assert_eq!(s3_object_results.len(), 2);
        assert_with(
            &s3_object_results[0],
            None,
            None,
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Deleted,
        );
        assert_with(
            &s3_object_results[1],
            None,
            None,
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Deleted,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_no_sequencer(pool: PgPool) {
        let ingester = test_ingester(pool);

        let events = replace_sequencers(test_events(None), None);
        ingester.ingest(S3(events)).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 2);
        assert_eq!(s3_object_results.len(), 2);
        assert_with(
            &s3_object_results[0],
            Some(0),
            None,
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Created,
        );
        assert_with(
            &s3_object_results[1],
            None,
            None,
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Deleted,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_multiple_matching_rows_created(pool: PgPool) {
        let ingester = test_ingester(pool);

        let events_one = replace_sequencers(
            test_events(Some(Created)),
            Some(EXPECTED_SEQUENCER_CREATED_ZERO.to_string()),
        );
        let events_two = test_events(Some(Created));
        let events_three = replace_sequencers(
            test_events(Some(Deleted)),
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
        );

        ingester.ingest(S3(events_one)).await.unwrap();
        ingester.ingest(S3(events_two)).await.unwrap();
        ingester.ingest(S3(events_three)).await.unwrap();

        let s3_object_results = fetch_results_ordered(&ingester).await;

        assert_eq!(s3_object_results.len(), 3);
        assert_with(
            &s3_object_results[0],
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_ZERO.to_string()),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Created,
        );
        assert_ingest_events(
            &s3_object_results[1],
            &s3_object_results[2],
            EXPECTED_VERSION_ID,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_multiple_matching_rows_deleted(pool: PgPool) {
        let ingester = test_ingester(pool);

        let events_one = replace_sequencers(
            test_events(Some(Deleted)),
            Some(EXPECTED_SEQUENCER_DELETED_TWO.to_string()),
        );
        let events_two = replace_sequencers(
            test_events(Some(Deleted)),
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
        );
        let events_three = test_events(Some(Created));

        ingester.ingest(S3(events_one)).await.unwrap();
        ingester.ingest(S3(events_two)).await.unwrap();
        ingester.ingest(S3(events_three)).await.unwrap();

        let s3_object_results = fetch_results_ordered(&ingester).await;

        assert_eq!(s3_object_results.len(), 3);
        assert_with(
            &s3_object_results[2],
            None,
            Some(EXPECTED_SEQUENCER_DELETED_TWO.to_string()),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Deleted,
        );
        assert_ingest_events(
            &s3_object_results[0],
            &s3_object_results[1],
            EXPECTED_VERSION_ID,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_permutations_small_without_version_id(pool: PgPool) {
        let event_permutations = vec![
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_default_version_id()
                .with_event_type(Created)
                .with_sequencer(Some("1".to_string())),
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_default_version_id()
                .with_event_type(Deleted)
                .with_sequencer(Some("2".to_string())),
            // Missing created event.
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_default_version_id()
                .with_event_type(Deleted)
                .with_sequencer(Some("3".to_string())),
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_default_version_id()
                .with_event_type(Created)
                .with_sequencer(Some("4".to_string())),
            // Missing deleted event.
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_default_version_id()
                .with_event_type(Created)
                .with_sequencer(Some("5".to_string())),
            // Different key
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key1".to_string())
                .with_default_version_id()
                .with_event_type(Created)
                .with_sequencer(Some("1".to_string())),
        ];

        let message = expected_message(
            None,
            FlatS3EventMessage::default_version_id(),
            false,
            Created,
        )
        .with_sha256(None)
        .with_e_tag(None)
        .with_last_modified_date(None);
        // 720 permutations
        run_permutation_test(&pool, event_permutations, 6, |s3_object_results| {
            assert_row(
                &s3_object_results[0],
                message.clone(),
                Some("1".to_string()),
                None,
            );
            assert_row(
                &s3_object_results[1],
                message.clone().with_key("key1".to_string()),
                Some("1".to_string()),
                None,
            );
            assert_row(
                &s3_object_results[2],
                message.clone().with_event_type(Deleted),
                Some("2".to_string()),
                None,
            );
            assert_row(
                &s3_object_results[3],
                message.clone().with_event_type(Deleted),
                Some("3".to_string()),
                None,
            );
            assert_row(
                &s3_object_results[4],
                message.clone(),
                Some("4".to_string()),
                None,
            );
            assert_row(
                &s3_object_results[5],
                message.clone(),
                Some("5".to_string()),
                None,
            );
        })
        .await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_permutations_small(pool: PgPool) {
        let event_permutations = example_event_permutations();

        let message = expected_message(None, "version_id".to_string(), false, Created)
            .with_sha256(None)
            .with_e_tag(None)
            .with_last_modified_date(None);
        // 720 permutations
        run_permutation_test(&pool, event_permutations, 5, |s3_object_results| {
            assert_row(
                &s3_object_results[0],
                message.clone(),
                Some("1".to_string()),
                None,
            );
            assert_row(
                &s3_object_results[1],
                message
                    .clone()
                    .with_version_id("version_id1".to_string())
                    .with_event_type(Deleted),
                Some("1".to_string()),
                None,
            );
            assert_row(
                &s3_object_results[2],
                message.clone().with_event_type(Deleted),
                Some("2".to_string()),
                None,
            );
            assert_row(
                &s3_object_results[3],
                message.clone(),
                Some("3".to_string()),
                None,
            );
            assert_row(
                &s3_object_results[4],
                message.clone().with_event_type(Deleted),
                Some("4".to_string()),
                None,
            );
        })
        .await;
    }

    pub(crate) fn assert_ingest_events(created: &PgRow, deleted: &PgRow, version_id: &str) {
        assert_with(
            created,
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            version_id.to_string(),
            Some(Default::default()),
            Created,
        );
        assert_with(
            deleted,
            None,
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            version_id.to_string(),
            Some(Default::default()),
            Deleted,
        );
    }

    fn example_event_permutations() -> Vec<FlatS3EventMessage> {
        vec![
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_version_id("version_id".to_string())
                .with_event_type(Created)
                .with_sequencer(Some("1".to_string())),
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_version_id("version_id".to_string())
                .with_event_type(Deleted)
                .with_sequencer(Some("2".to_string())),
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_version_id("version_id".to_string())
                .with_event_type(Created)
                .with_sequencer(Some("3".to_string())),
            // Duplicate
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_version_id("version_id".to_string())
                .with_event_type(Created)
                .with_sequencer(Some("3".to_string())),
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_version_id("version_id".to_string())
                .with_event_type(Deleted)
                .with_sequencer(Some("4".to_string())),
            // Different version id
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_version_id("version_id1".to_string())
                .with_event_type(Deleted)
                .with_sequencer(Some("1".to_string())),
        ]
    }

    async fn run_permutation_test<F>(
        pool: &PgPool,
        permutations: Vec<FlatS3EventMessage>,
        expected_rows: usize,
        row_asserts: F,
    ) where
        F: Fn(Vec<PgRow>),
    {
        let now = Instant::now();

        let length = permutations.len();
        for events in permutations.into_iter().permutations(length) {
            let ingester = test_ingester(pool.clone());

            for chunk in events.chunks(1) {
                ingester
                    .ingest(EventSourceType::S3(
                        // Okay to dedup here as the Lambda function would be doing this anyway.
                        FlatS3EventMessages(chunk.to_vec()).dedup().into(),
                    ))
                    .await
                    .unwrap();
            }

            let s3_object_results = fetch_results_ordered(&ingester).await;

            assert_eq!(s3_object_results.len(), expected_rows);

            row_asserts(s3_object_results);

            // Clean up for next permutation.
            pool.execute("truncate s3_object, object_group")
                .await
                .unwrap();
        }

        println!(
            "permutation test took: {} seconds",
            now.elapsed().as_secs_f32()
        );
    }

    fn assert_missing_deleted(created: &PgRow, deleted: &PgRow, version_id: &str) {
        assert_with(
            created,
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            version_id.to_string(),
            Some(Default::default()),
            Created,
        );
        assert_with(
            deleted,
            Some(0),
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            version_id.to_string(),
            Some(Default::default()),
            Created,
        );
    }

    fn assert_missing_created(deleted: &PgRow, created: &PgRow, version_id: &str) {
        assert_with(
            deleted,
            None,
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            version_id.to_string(),
            Some(Default::default()),
            Deleted,
        );
        assert_with(
            created,
            None,
            Some(EXPECTED_SEQUENCER_DELETED_TWO.to_string()),
            version_id.to_string(),
            Some(Default::default()),
            Deleted,
        );
    }

    pub(crate) fn remove_version_ids(
        mut events: TransposedS3EventMessages,
    ) -> TransposedS3EventMessages {
        events
            .version_ids
            .iter_mut()
            .for_each(|version_id| *version_id = FlatS3EventMessage::default_version_id());

        events
    }

    pub(crate) fn replace_sequencers(
        mut events: TransposedS3EventMessages,
        sequencer: Option<String>,
    ) -> TransposedS3EventMessages {
        events
            .sequencers
            .iter_mut()
            .for_each(|replace_sequencer| replace_sequencer.clone_from(&sequencer));

        events
    }

    pub(crate) async fn fetch_results<'a>(client: &Client) -> (Vec<PgRow>, Vec<PgRow>) {
        (
            sqlx::query("select * from object_group")
                .fetch_all(client.pool())
                .await
                .unwrap(),
            sqlx::query("select * from s3_object")
                .fetch_all(client.pool())
                .await
                .unwrap(),
        )
    }

    pub(crate) async fn fetch_results_ordered<'a>(client: &Client) -> Vec<PgRow> {
        sqlx::query("select * from s3_object order by sequencer, key, version_id")
            .fetch_all(client.pool())
            .await
            .unwrap()
    }

    pub(crate) fn assert_created(s3_object_results: &PgRow) {
        assert_with(
            s3_object_results,
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Created,
        )
    }

    pub(crate) fn assert_row(
        s3_object_results: &PgRow,
        message: FlatS3EventMessage,
        sequencer: Option<String>,
        date: Option<DateTime<Utc>>,
    ) {
        assert_ne!(
            s3_object_results.get::<Uuid, _>("s3_object_id"),
            s3_object_results.get::<Uuid, _>("public_id")
        );
        assert_eq!(message.bucket, s3_object_results.get::<String, _>("bucket"));
        assert_eq!(message.key, s3_object_results.get::<String, _>("key"));
        assert_eq!(
            message.version_id,
            s3_object_results.get::<String, _>("version_id")
        );
        assert_eq!(
            sequencer,
            s3_object_results.get::<Option<String>, _>("sequencer")
        );
        assert_eq!(
            message.size,
            s3_object_results.get::<Option<i64>, _>("size")
        );
        assert_eq!(
            message.sha256,
            s3_object_results.get::<Option<String>, _>("sha256")
        );
        assert_eq!(
            message.e_tag,
            s3_object_results.get::<Option<String>, _>("e_tag")
        );
        assert_eq!(
            message.last_modified_date,
            s3_object_results.get::<Option<DateTime<Utc>>, _>("last_modified_date")
        );
        assert_eq!(
            date,
            s3_object_results.get::<Option<DateTime<Utc>>, _>("date")
        );
        assert_eq!(
            message.is_delete_marker,
            s3_object_results.get::<bool, _>("is_delete_marker")
        );
        assert_eq!(
            message.event_type,
            s3_object_results.get::<EventType, _>("event_type")
        );
    }

    pub(crate) fn expected_message(
        size: Option<i64>,
        version_id: String,
        is_delete_marker: bool,
        event_type: EventType,
    ) -> FlatS3EventMessage {
        FlatS3EventMessage::default()
            .with_bucket("bucket".to_string())
            .with_key("key".to_string())
            .with_size(size)
            .with_version_id(version_id)
            .with_last_modified_date(Some(DateTime::<Utc>::default()))
            .with_e_tag(Some(EXPECTED_E_TAG.to_string()))
            .with_sha256(Some(EXPECTED_SHA256.to_string()))
            .with_is_delete_marker(is_delete_marker)
            .with_event_type(event_type)
    }

    pub(crate) fn assert_with(
        s3_object_results: &PgRow,
        size: Option<i64>,
        sequencer: Option<String>,
        version_id: String,
        date: Option<DateTime<Utc>>,
        event_type: EventType,
    ) {
        let message = expected_message(size, version_id, false, event_type);

        assert_row(s3_object_results, message, sequencer, date);
    }

    fn update_test_events(mut events: TransposedS3EventMessages) -> TransposedS3EventMessages {
        let update_last_modified = |dates: &mut Vec<Option<DateTime<Utc>>>| {
            dates.iter_mut().for_each(|last_modified| {
                *last_modified = Some(DateTime::default());
            });
        };
        let update_storage_class = |classes: &mut Vec<Option<StorageClass>>| {
            classes.iter_mut().for_each(|storage_class| {
                *storage_class = Some(StorageClass::Standard);
            });
        };
        let update_sha256 = |sha256s: &mut Vec<Option<String>>| {
            sha256s.iter_mut().for_each(|sha256| {
                *sha256 = Some(EXPECTED_SHA256.to_string());
            });
        };

        update_last_modified(&mut events.last_modified_dates);
        update_storage_class(&mut events.storage_classes);
        update_sha256(&mut events.sha256s);

        events
    }

    pub(crate) fn test_events(filter_by: Option<EventType>) -> TransposedS3EventMessages {
        FlatS3EventMessages(
            FlatS3EventMessages::from(update_test_events(expected_events_simple()))
                .0
                .into_iter()
                .filter(|event| {
                    filter_by.is_none() || &event.event_type == filter_by.as_ref().unwrap()
                })
                .collect(),
        )
        .into()
    }

    pub(crate) fn test_events_delete_marker() -> TransposedS3EventMessages {
        update_test_events(expected_events_simple_delete_marker())
    }

    pub(crate) fn test_ingester(pool: PgPool) -> Client {
        Client::from_pool(pool)
    }
}
