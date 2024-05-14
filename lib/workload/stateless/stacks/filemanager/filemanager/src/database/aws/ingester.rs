//! This module handles logic associated with event ingestion.
//!

use async_trait::async_trait;
use chrono::{DateTime, Utc};
use sqlx::{query_file, query_file_as};
use tracing::{debug, trace};
use uuid::Uuid;

use crate::database::{Client, CredentialGenerator, Ingest};
use crate::error::Result;
use crate::events::aws::message::EventType;
use crate::events::aws::{Events, TransposedS3EventMessages};
use crate::events::aws::{FlatS3EventMessage, FlatS3EventMessages, StorageClass};
use crate::events::EventSourceType;
use crate::uuid::UuidGenerator;

/// An ingester for S3 events.
#[derive(Debug)]
pub struct Ingester<'a> {
    client: Client<'a>,
}

/// The type representing an insert query.
#[derive(Debug)]
struct Insert {
    object_id: Uuid,
    number_duplicate_events: i64,
}

impl<'a> Ingester<'a> {
    /// Create a new ingester.
    pub fn new(client: Client<'a>) -> Self {
        Self { client }
    }

    /// Create a new ingester with a default database client.
    pub async fn with_defaults(generator: Option<impl CredentialGenerator>) -> Result<Self> {
        Ok(Self {
            client: Client::from_generator(generator).await?,
        })
    }

    fn reprocess_updated(
        messages: TransposedS3EventMessages,
        updated: Vec<FlatS3EventMessage>,
    ) -> TransposedS3EventMessages {
        if updated.is_empty() {
            return messages;
        }

        // Now, events with a sequencer value need to be reprocessed.
        let mut flat_object_created = FlatS3EventMessages::from(messages).into_inner();
        let mut reprocess = FlatS3EventMessages(updated).into_inner();

        flat_object_created.retain_mut(|object| {
            // If the sequencer is null, then we remove this object has it has already been consumed. Otherwise,
            // we keep it, and potentially replace an existing object.
            if let Some(pos) = reprocess
                .iter()
                .position(|reprocess| reprocess.s3_object_id == object.s3_object_id)
            {
                let reprocess = reprocess.remove(pos);
                if reprocess.sequencer.is_none() {
                    // No re-processing if the sequencer was never set.
                    return false;
                } else {
                    *object = reprocess;
                }
            }

            debug!(
                s3_object_id = ?object.s3_object_id,
                number_duplicate_events = object.number_reordered,
                "out of order event found"
            );

            true
        });

        TransposedS3EventMessages::from(FlatS3EventMessages(flat_object_created).sort_and_dedup())
    }

    fn reprocess_inserts(object_ids: Vec<Uuid>, inserted: &mut Vec<Insert>) -> Vec<Uuid> {
        object_ids
            .into_iter()
            .rev()
            .flat_map(|object_id| {
                // If we cannot find the object in our new ids, this object already exists.
                let pos = inserted.iter().rposition(|record| {
                    // This will never be `None`, maybe this is an sqlx bug?
                    record.object_id == object_id
                })?;

                // We can remove this to avoid searching over it again.
                let record = inserted.remove(pos);
                debug!(
                    object_id = ?record.object_id,
                    number_duplicate_events = record.number_duplicate_events,
                    "duplicate event found"
                );

                // This is a new event so the corresponding object should be inserted.
                Some(object_id)
            })
            .collect()
    }

    /// Ingest the events into the database by calling the insert and update queries.
    pub async fn ingest_events(&self, events: Events) -> Result<()> {
        let Events {
            object_created,
            object_deleted,
            ..
        } = events;

        trace!(object_created = ?object_created, "ingesting object created events");

        let mut tx = self.client().pool().begin().await?;

        // First, try and update existing events to remove any un-ordered events.
        let updated = query_file_as!(
            FlatS3EventMessage,
            "../database/queries/ingester/aws/update_reordered_for_created.sql",
            &object_created.s3_object_ids,
            &object_created.buckets,
            &object_created.keys,
            &object_created.event_times as &[Option<DateTime<Utc>>],
            &object_created.sizes as &[Option<i64>],
            &object_created.sha256s as &[Option<String>],
            &object_created.last_modified_dates as &[Option<DateTime<Utc>>],
            &object_created.e_tags as &[Option<String>],
            &object_created.storage_classes as &[Option<StorageClass>],
            &object_created.version_ids as &[String],
            &object_created.sequencers as &[Option<String>]
        )
        .fetch_all(&mut *tx)
        .await?;

        let object_created = Self::reprocess_updated(object_created, updated);
        let object_ids = UuidGenerator::generate_n(object_created.s3_object_ids.len());

        let mut inserted = query_file_as!(
            Insert,
            "../database/queries/ingester/aws/insert_s3_created_objects.sql",
            &object_created.s3_object_ids,
            &object_ids,
            &UuidGenerator::generate_n(object_created.s3_object_ids.len()),
            &object_created.buckets,
            &object_created.keys,
            &object_created.event_times as &[Option<DateTime<Utc>>],
            &object_created.sizes as &[Option<i64>],
            &object_created.sha256s as &[Option<String>],
            &object_created.last_modified_dates as &[Option<DateTime<Utc>>],
            &object_created.e_tags as &[Option<String>],
            &object_created.storage_classes as &[Option<StorageClass>],
            &object_created.version_ids,
            &object_created.sequencers as &[Option<String>]
        )
        .fetch_all(&mut *tx)
        .await?;

        let object_ids = Self::reprocess_inserts(object_ids, &mut inserted);

        // Insert only the non duplicate events.
        if !object_ids.is_empty() {
            debug!(
                object_ids = ?object_ids,
                "inserting into object table created events"
            );

            query_file!(
                "../database/queries/ingester/insert_objects.sql",
                &object_ids,
            )
            .execute(&mut *tx)
            .await?;
        }

        trace!(object_removed = ?object_deleted, "ingesting object removed events");

        // First, try and update existing events to remove any un-ordered events.
        let updated = query_file_as!(
            FlatS3EventMessage,
            "../database/queries/ingester/aws/update_reordered_for_deleted.sql",
            &object_deleted.s3_object_ids,
            &object_deleted.buckets,
            &object_deleted.keys,
            &object_deleted.event_times as &[Option<DateTime<Utc>>],
            &object_deleted.version_ids,
            &object_deleted.sequencers as &[Option<String>],
        )
        .fetch_all(&mut *tx)
        .await?;

        let object_deleted = Self::reprocess_updated(object_deleted, updated);
        let object_ids = UuidGenerator::generate_n(object_deleted.s3_object_ids.len());

        let mut inserted = query_file_as!(
            Insert,
            "../database/queries/ingester/aws/insert_s3_deleted_objects.sql",
            &object_deleted.s3_object_ids,
            &object_ids,
            &UuidGenerator::generate_n(object_deleted.s3_object_ids.len()),
            &object_deleted.buckets,
            &object_deleted.keys,
            &object_deleted.event_times as &[Option<DateTime<Utc>>],
            &object_deleted.sizes as &[Option<i64>],
            &object_deleted.sha256s as &[Option<String>],
            &object_deleted.last_modified_dates as &[Option<DateTime<Utc>>],
            &object_deleted.e_tags as &[Option<String>],
            &object_deleted.storage_classes as &[Option<StorageClass>],
            &object_deleted.version_ids,
            &object_deleted.sequencers as &[Option<String>],
            // Fill this with 1 reorder, because if we get here then this must be a reordered event.
            &vec![1; object_deleted.s3_object_ids.len()]
        )
        .fetch_all(&mut *tx)
        .await?;

        let object_ids = Self::reprocess_inserts(object_ids, &mut inserted);

        // Insert only the non duplicate events.
        if !object_ids.is_empty() {
            debug!(
                object_ids = ?object_ids,
                "inserting into object table from deleted events"
            );

            query_file!(
                "../database/queries/ingester/insert_objects.sql",
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

#[async_trait]
impl<'a> Ingest for Ingester<'a> {
    async fn ingest(&self, events: EventSourceType) -> Result<()> {
        match events {
            EventSourceType::S3(events) => self.ingest_events(events).await,
        }
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

    use crate::database::aws::ingester::Ingester;
    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::{Client, Ingest};
    use crate::events::aws::message::EventType::{Created, Deleted};
    use crate::events::aws::tests::{
        expected_events_simple, expected_flat_events_simple, EXPECTED_E_TAG,
        EXPECTED_SEQUENCER_CREATED_ONE, EXPECTED_SEQUENCER_CREATED_ZERO,
        EXPECTED_SEQUENCER_DELETED_ONE, EXPECTED_SEQUENCER_DELETED_TWO, EXPECTED_SHA256,
        EXPECTED_VERSION_ID,
    };
    use crate::events::aws::{Events, FlatS3EventMessage, FlatS3EventMessages, StorageClass};
    use crate::events::EventSourceType;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_created(pool: PgPool) {
        let mut events = test_events();
        events.object_deleted = Default::default();

        let ingester = test_ingester(pool);
        ingester.ingest_events(events).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 1);
        assert_eq!(s3_object_results.len(), 1);
        assert_created(&s3_object_results[0]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_created_large_size(pool: PgPool) {
        let mut events = test_events();
        events.object_deleted = Default::default();

        events
            .object_created
            .sizes
            .iter_mut()
            .for_each(|size| *size = Some(i64::MAX));

        let ingester = test_ingester(pool);
        ingester.ingest_events(events).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 1);
        assert_eq!(s3_object_results.len(), 1);
        assert_with(
            &s3_object_results[0],
            Some(i64::MAX),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            None,
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            None,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_removed(pool: PgPool) {
        let events = test_events();

        let ingester = test_ingester(pool);
        ingester.ingest_events(events).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 1);
        assert_eq!(s3_object_results.len(), 1);
        assert_ingest_events(&s3_object_results[0], EXPECTED_VERSION_ID);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest(pool: PgPool) {
        let events = test_events();

        let ingester = test_ingester(pool);
        ingester.ingest(EventSourceType::S3(events)).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 1);
        assert_eq!(s3_object_results.len(), 1);
        assert_ingest_events(&s3_object_results[0], EXPECTED_VERSION_ID);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_duplicates(pool: PgPool) {
        let ingester = test_ingester(pool);
        ingester
            .ingest(EventSourceType::S3(test_events()))
            .await
            .unwrap();
        ingester
            .ingest(EventSourceType::S3(test_events()))
            .await
            .unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 1);
        assert_eq!(s3_object_results.len(), 1);
        assert_eq!(
            2,
            s3_object_results[0].get::<i64, _>("number_duplicate_events")
        );
        assert_ingest_events(&s3_object_results[0], EXPECTED_VERSION_ID);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_created_multiple_object_ids(pool: PgPool) {
        let ingester = test_ingester(pool);
        let mut events_one = test_events();
        events_one.object_deleted = Default::default();

        let events_two = replace_sequencers(
            test_events(),
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
        );
        // Merge events into same ingestion.
        let flat_events = FlatS3EventMessages::from(events_two.object_created);
        flat_events
            .into_inner()
            .into_iter()
            .for_each(|event| events_one.object_created.push(event));

        ingester
            .ingest(EventSourceType::S3(events_one))
            .await
            .unwrap();

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
    async fn ingest_deleted_multiple_object_ids(pool: PgPool) {
        let ingester = test_ingester(pool);
        let mut events_one = test_events();
        events_one.object_created = Default::default();

        let events_two = replace_sequencers(
            test_events(),
            Some(EXPECTED_SEQUENCER_DELETED_TWO.to_string()),
        );
        // Merge events into same ingestion.
        let flat_events = FlatS3EventMessages::from(events_two.object_deleted);
        flat_events
            .into_inner()
            .into_iter()
            .for_each(|event| events_one.object_deleted.push(event));

        ingester
            .ingest(EventSourceType::S3(events_one))
            .await
            .unwrap();

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
    async fn ingest_reordered_duplicates(pool: PgPool) {
        let ingester = test_ingester(pool);
        ingester
            .ingest(EventSourceType::S3(test_events()))
            .await
            .unwrap();

        // No reason the order should matter if they are duplicates
        let events = test_events();
        ingester
            .ingest(EventSourceType::S3(
                Events::default().with_object_deleted(events.object_deleted),
            ))
            .await
            .unwrap();
        ingester
            .ingest(EventSourceType::S3(
                Events::default().with_object_created(events.object_created),
            ))
            .await
            .unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 1);
        assert_eq!(s3_object_results.len(), 1);
        assert_eq!(
            2,
            s3_object_results[0].get::<i64, _>("number_duplicate_events")
        );
        assert_ingest_events(&s3_object_results[0], EXPECTED_VERSION_ID);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_reorder(pool: PgPool) {
        let ingester = test_ingester(pool);
        let events = test_events();
        // Deleted coming before created.
        ingester
            .ingest(EventSourceType::S3(
                Events::default().with_object_deleted(events.object_deleted),
            ))
            .await
            .unwrap();
        ingester
            .ingest(EventSourceType::S3(
                Events::default().with_object_created(events.object_created),
            ))
            .await
            .unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 1);
        assert_eq!(s3_object_results.len(), 1);
        assert_eq!(2, s3_object_results[0].get::<i64, _>("number_reordered"));
        assert_ingest_events(&s3_object_results[0], EXPECTED_VERSION_ID);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_reorder_and_duplicates_complex(pool: PgPool) {
        let ingester = test_ingester(pool);
        ingester
            .ingest(EventSourceType::S3(test_events()))
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

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 2);
        assert_eq!(s3_object_results.len(), 2);
        assert_eq!(
            0,
            s3_object_results[0].get::<i64, _>("number_duplicate_events")
        );
        assert_eq!(0, s3_object_results[0].get::<i64, _>("number_reordered"));
        assert_eq!(
            1,
            s3_object_results[1].get::<i64, _>("number_duplicate_events")
        );
        assert_eq!(1, s3_object_results[1].get::<i64, _>("number_reordered"));
        assert_with(
            &s3_object_results[0],
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            None,
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            None,
        );
        assert_with(
            &s3_object_results[1],
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string().add("7")),
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Some(Default::default()),
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_without_version_id(pool: PgPool) {
        let ingester = test_ingester(pool);
        let events = remove_version_ids(test_events());

        // Correct ordering
        ingester
            .ingest(EventSourceType::S3(
                Events::default().with_object_created(events.object_created),
            ))
            .await
            .unwrap();
        ingester
            .ingest(EventSourceType::S3(
                Events::default().with_object_deleted(events.object_deleted),
            ))
            .await
            .unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 1);
        assert_eq!(s3_object_results.len(), 1);
        assert_eq!(0, s3_object_results[0].get::<i64, _>("number_reordered"));
        assert_ingest_events(
            &s3_object_results[0],
            &FlatS3EventMessage::default_version_id(),
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_duplicates_without_version_id(pool: PgPool) {
        let ingester = test_ingester(pool);
        ingester
            .ingest(EventSourceType::S3(remove_version_ids(test_events())))
            .await
            .unwrap();
        ingester
            .ingest(EventSourceType::S3(remove_version_ids(test_events())))
            .await
            .unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 1);
        assert_eq!(s3_object_results.len(), 1);
        assert_eq!(
            2,
            s3_object_results[0].get::<i64, _>("number_duplicate_events")
        );
        assert_ingest_events(
            &s3_object_results[0],
            &FlatS3EventMessage::default_version_id(),
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_reordered_duplicates_without_version_id(pool: PgPool) {
        let ingester = test_ingester(pool);
        ingester
            .ingest(EventSourceType::S3(remove_version_ids(test_events())))
            .await
            .unwrap();

        // No reason the order should matter if they are duplicates
        let events = remove_version_ids(test_events());
        ingester
            .ingest(EventSourceType::S3(
                Events::default().with_object_deleted(events.object_deleted),
            ))
            .await
            .unwrap();
        ingester
            .ingest(EventSourceType::S3(
                Events::default().with_object_created(events.object_created),
            ))
            .await
            .unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 1);
        assert_eq!(s3_object_results.len(), 1);
        assert_eq!(
            2,
            s3_object_results[0].get::<i64, _>("number_duplicate_events")
        );
        assert_ingest_events(
            &s3_object_results[0],
            &FlatS3EventMessage::default_version_id(),
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_reorder_without_version_id(pool: PgPool) {
        let ingester = test_ingester(pool);
        let events = remove_version_ids(test_events());

        // Deleted coming before created.
        ingester
            .ingest(EventSourceType::S3(
                Events::default().with_object_deleted(events.object_deleted),
            ))
            .await
            .unwrap();
        ingester
            .ingest(EventSourceType::S3(
                Events::default().with_object_created(events.object_created),
            ))
            .await
            .unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 1);
        assert_eq!(s3_object_results.len(), 1);
        assert_eq!(2, s3_object_results[0].get::<i64, _>("number_reordered"));
        assert_with(
            &s3_object_results[0],
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            FlatS3EventMessage::default_version_id(),
            Some(Default::default()),
            Some(Default::default()),
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_duplicates_with_version_id(pool: PgPool) {
        let ingester = test_ingester(pool);
        ingester
            .ingest(EventSourceType::S3(test_events()))
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

        assert_eq!(object_results.len(), 2);
        assert_eq!(s3_object_results.len(), 2);
        assert_eq!(
            0,
            s3_object_results[0].get::<i64, _>("number_duplicate_events")
        );
        assert_eq!(0, s3_object_results[0].get::<i64, _>("number_reordered"));
        assert_eq!(
            2,
            s3_object_results[1].get::<i64, _>("number_duplicate_events")
        );
        assert_eq!(0, s3_object_results[1].get::<i64, _>("number_reordered"));
        assert_with(
            &s3_object_results[1],
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Some(Default::default()),
        );
        assert_with(
            &s3_object_results[0],
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            None,
            "version_id".to_string(),
            Some(Default::default()),
            None,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_missing_deleted(pool: PgPool) {
        let ingester = test_ingester(pool);

        let mut events_one = test_events();
        // Missing deleted event.
        events_one.object_deleted = Default::default();

        // New created event with a higher sequencer.
        let mut events_two = replace_sequencers(
            test_events(),
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
        );
        events_two.object_deleted = Default::default();

        ingester.ingest_events(events_one).await.unwrap();
        ingester.ingest_events(events_two).await.unwrap();

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

        let mut events_one = test_events();
        // Missing deleted event.
        events_one.object_deleted = Default::default();

        // New created event with a higher sequencer.
        let mut events_two = replace_sequencers(
            test_events(),
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
        );
        events_two.object_deleted = Default::default();

        // Reorder
        ingester.ingest_events(events_two).await.unwrap();
        ingester.ingest_events(events_one).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 2);
        assert_eq!(s3_object_results.len(), 2);
        assert_missing_deleted(
            &s3_object_results[1],
            &s3_object_results[0],
            EXPECTED_VERSION_ID,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_missing_created(pool: PgPool) {
        let ingester = test_ingester(pool);

        let mut events_one = test_events();
        // Missing created event.
        events_one.object_created = Default::default();

        // New deleted event with a higher sequencer.
        let mut events_two = replace_sequencers(
            test_events(),
            Some(EXPECTED_SEQUENCER_DELETED_TWO.to_string()),
        );
        events_two.object_created = Default::default();

        ingester.ingest_events(events_one).await.unwrap();
        ingester.ingest_events(events_two).await.unwrap();

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

        let mut events_one = test_events();
        // Missing created event.
        events_one.object_created = Default::default();

        // New deleted event with a higher sequencer.
        let mut events_two = replace_sequencers(
            test_events(),
            Some(EXPECTED_SEQUENCER_DELETED_TWO.to_string()),
        );
        events_two.object_created = Default::default();

        // Reorder
        ingester.ingest_events(events_two).await.unwrap();
        ingester.ingest_events(events_one).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 2);
        assert_eq!(s3_object_results.len(), 2);
        assert_missing_created(
            &s3_object_results[1],
            &s3_object_results[0],
            EXPECTED_VERSION_ID,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_missing_deleted_without_version_id(pool: PgPool) {
        let ingester = test_ingester(pool);

        let mut events_one = remove_version_ids(test_events());
        // Missing deleted event.
        events_one.object_deleted = Default::default();

        // New created event with a higher sequencer.
        let mut events_two = replace_sequencers(
            remove_version_ids(test_events()),
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
        );
        events_two.object_deleted = Default::default();

        ingester.ingest_events(events_one).await.unwrap();
        ingester.ingest_events(events_two).await.unwrap();

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

        let mut events_one = remove_version_ids(test_events());
        // Missing deleted event.
        events_one.object_deleted = Default::default();

        // New created event with a higher sequencer.
        let mut events_two = replace_sequencers(
            remove_version_ids(test_events()),
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
        );
        events_two.object_deleted = Default::default();

        // Reorder
        ingester.ingest_events(events_two).await.unwrap();
        ingester.ingest_events(events_one).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 2);
        assert_eq!(s3_object_results.len(), 2);
        assert_missing_deleted(
            &s3_object_results[1],
            &s3_object_results[0],
            &FlatS3EventMessage::default_version_id(),
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_missing_created_without_version_id(pool: PgPool) {
        let ingester = test_ingester(pool);

        let mut events_one = remove_version_ids(test_events());
        // Missing created event.
        events_one.object_created = Default::default();

        // New deleted event with a higher sequencer.
        let mut events_two = replace_sequencers(
            remove_version_ids(test_events()),
            Some(EXPECTED_SEQUENCER_DELETED_TWO.to_string()),
        );
        events_two.object_created = Default::default();

        ingester.ingest_events(events_one).await.unwrap();
        ingester.ingest_events(events_two).await.unwrap();

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

        let mut events_one = remove_version_ids(test_events());
        // Missing created event.
        events_one.object_created = Default::default();

        // New deleted event with a higher sequencer.
        let mut events_two = replace_sequencers(
            remove_version_ids(test_events()),
            Some(EXPECTED_SEQUENCER_DELETED_TWO.to_string()),
        );
        events_two.object_created = Default::default();

        // Reorder
        ingester.ingest_events(events_two).await.unwrap();
        ingester.ingest_events(events_one).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 2);
        assert_eq!(s3_object_results.len(), 2);
        assert_missing_created(
            &s3_object_results[1],
            &s3_object_results[0],
            &FlatS3EventMessage::default_version_id(),
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_no_sequencer_created(pool: PgPool) {
        let ingester = test_ingester(pool);

        let mut events_one = replace_sequencers(test_events(), None);
        events_one.object_deleted = Default::default();

        let mut events_two = replace_sequencers(test_events(), None);
        events_two.object_deleted = Default::default();

        ingester.ingest_events(events_one).await.unwrap();
        ingester.ingest_events(events_two).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 2);
        assert_eq!(s3_object_results.len(), 2);
        assert_with(
            &s3_object_results[0],
            Some(0),
            None,
            None,
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            None,
        );
        assert_with(
            &s3_object_results[1],
            Some(0),
            None,
            None,
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            None,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_no_sequencer_deleted(pool: PgPool) {
        let ingester = test_ingester(pool);

        let mut events_one = replace_sequencers(test_events(), None);
        events_one.object_created = Default::default();

        let mut events_two = replace_sequencers(test_events(), None);
        events_two.object_created = Default::default();

        ingester.ingest_events(events_one).await.unwrap();
        ingester.ingest_events(events_two).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 2);
        assert_eq!(s3_object_results.len(), 2);
        assert_with(
            &s3_object_results[0],
            None,
            None,
            None,
            EXPECTED_VERSION_ID.to_string(),
            None,
            Some(Default::default()),
        );
        assert_with(
            &s3_object_results[1],
            None,
            None,
            None,
            EXPECTED_VERSION_ID.to_string(),
            None,
            Some(Default::default()),
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_no_sequencer(pool: PgPool) {
        let ingester = test_ingester(pool);

        let events = replace_sequencers(test_events(), None);
        ingester.ingest_events(events).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 2);
        assert_eq!(s3_object_results.len(), 2);
        assert_with(
            &s3_object_results[0],
            Some(0),
            None,
            None,
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            None,
        );
        assert_with(
            &s3_object_results[1],
            None,
            None,
            None,
            EXPECTED_VERSION_ID.to_string(),
            None,
            Some(Default::default()),
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_multiple_matching_rows_created(pool: PgPool) {
        let ingester = test_ingester(pool);

        let mut events_one = replace_sequencers(
            test_events(),
            Some(EXPECTED_SEQUENCER_CREATED_ZERO.to_string()),
        );
        // Missing deleted event.
        events_one.object_deleted = Default::default();

        // New created event with a higher sequencer.
        let mut events_two = test_events();
        events_two.object_deleted = Default::default();

        // Next event matches both the above when checking sequencer condition.
        let mut events_three = replace_sequencers(
            test_events(),
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
        );
        events_three.object_created = Default::default();

        ingester.ingest_events(events_one).await.unwrap();
        ingester.ingest_events(events_two).await.unwrap();
        ingester.ingest_events(events_three).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 2);
        assert_eq!(s3_object_results.len(), 2);
        assert_with(
            &s3_object_results[0],
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_ZERO.to_string()),
            None,
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            None,
        );
        assert_ingest_events(&s3_object_results[1], EXPECTED_VERSION_ID);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_multiple_matching_rows_deleted(pool: PgPool) {
        let ingester = test_ingester(pool);

        let mut events_one = replace_sequencers(
            test_events(),
            Some(EXPECTED_SEQUENCER_DELETED_TWO.to_string()),
        );
        // Missing created event.
        events_one.object_created = Default::default();

        // New deleted event with a higher sequencer.
        let mut events_two = replace_sequencers(
            test_events(),
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
        );
        events_two.object_created = Default::default();

        // Next event matches both the above when checking sequencer condition.
        let mut events_three = test_events();
        events_three.object_deleted = Default::default();

        ingester.ingest_events(events_one).await.unwrap();
        ingester.ingest_events(events_two).await.unwrap();
        ingester.ingest_events(events_three).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 2);
        assert_eq!(s3_object_results.len(), 2);
        assert_with(
            &s3_object_results[0],
            None,
            None,
            Some(EXPECTED_SEQUENCER_DELETED_TWO.to_string()),
            EXPECTED_VERSION_ID.to_string(),
            None,
            Some(Default::default()),
        );
        assert_ingest_events(&s3_object_results[1], EXPECTED_VERSION_ID);
    }

    pub(crate) fn assert_ingest_events(result: &PgRow, version_id: &str) {
        assert_with(
            result,
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            version_id.to_string(),
            Some(Default::default()),
            Some(Default::default()),
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

        // 720 permutations
        run_permutation_test(&pool, event_permutations, 5, |s3_object_results| {
            find_object_with(
                &s3_object_results,
                "key",
                "bucket",
                &FlatS3EventMessage::default_version_id(),
                Some("1"),
                Some("2"),
            )
            .unwrap();
            find_object_with(
                &s3_object_results,
                "key",
                "bucket",
                &FlatS3EventMessage::default_version_id(),
                None,
                Some("3"),
            )
            .unwrap();
            find_object_with(
                &s3_object_results,
                "key",
                "bucket",
                &FlatS3EventMessage::default_version_id(),
                Some("4"),
                None,
            )
            .unwrap();
            find_object_with(
                &s3_object_results,
                "key",
                "bucket",
                &FlatS3EventMessage::default_version_id(),
                Some("5"),
                None,
            )
            .unwrap();
            find_object_with(
                &s3_object_results,
                "key1",
                "bucket",
                &FlatS3EventMessage::default_version_id(),
                Some("1"),
                None,
            )
            .unwrap();
        })
        .await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_permutations_small(pool: PgPool) {
        let event_permutations = example_event_permutations();

        // 720 permutations
        run_permutation_test(&pool, event_permutations, 3, |s3_object_results| {
            find_object_with(
                &s3_object_results,
                "key",
                "bucket",
                "version_id",
                Some("1"),
                Some("2"),
            )
            .unwrap();
            find_object_with(
                &s3_object_results,
                "key",
                "bucket",
                "version_id",
                Some("3"),
                Some("4"),
            )
            .unwrap();
            find_object_with(
                &s3_object_results,
                "key",
                "bucket",
                "version_id1",
                None,
                Some("1"),
            )
            .unwrap();
        })
        .await;
    }

    #[ignore]
    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_permutations(pool: PgPool) {
        // This primarily tests out of order and duplicate event ingestion, however it could also function
        // as a performance test.
        let mut event_permutations = example_event_permutations();
        event_permutations.extend(vec![
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_version_id("version_id".to_string())
                .with_event_type(Created)
                .with_sequencer(Some("5".to_string())),
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_version_id("version_id".to_string())
                .with_event_type(Deleted)
                .with_sequencer(Some("6".to_string())),
        ]);

        // 40320 permutations
        run_permutation_test(&pool, event_permutations, 4, |s3_object_results| {
            find_object_with(
                &s3_object_results,
                "key",
                "bucket",
                "version_id",
                Some("1"),
                Some("2"),
            )
            .unwrap();
            find_object_with(
                &s3_object_results,
                "key",
                "bucket",
                "version_id",
                Some("3"),
                Some("4"),
            )
            .unwrap();
            find_object_with(
                &s3_object_results,
                "key",
                "bucket",
                "version_id",
                Some("5"),
                Some("6"),
            )
            .unwrap();
            find_object_with(
                &s3_object_results,
                "key",
                "bucket",
                "version_id1",
                None,
                Some("1"),
            )
            .unwrap();
        })
        .await;
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

    fn find_object_with<'a>(
        results: &'a [PgRow],
        key: &str,
        bucket: &str,
        version_id: &str,
        created_sequencer: Option<&str>,
        deleted_sequencer: Option<&str>,
    ) -> Option<&'a PgRow> {
        results.iter().find(|object| {
            object.get::<String, _>("key") == key
                && object.get::<String, _>("bucket") == bucket
                && object.get::<String, _>("version_id") == version_id
                && object.get::<Option<&str>, _>("created_sequencer") == created_sequencer
                && object.get::<Option<&str>, _>("deleted_sequencer") == deleted_sequencer
        })
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

            let (object_results, s3_object_results) = fetch_results(&ingester).await;

            assert_eq!(object_results.len(), expected_rows);
            assert_eq!(s3_object_results.len(), expected_rows);

            row_asserts(s3_object_results);

            // Clean up for next permutation.
            pool.execute("truncate s3_object, object").await.unwrap();
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
            None,
            version_id.to_string(),
            Some(Default::default()),
            None,
        );
        assert_with(
            deleted,
            Some(0),
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            None,
            version_id.to_string(),
            Some(Default::default()),
            None,
        );
    }

    fn assert_missing_created(created: &PgRow, deleted: &PgRow, version_id: &str) {
        assert_with(
            created,
            None,
            None,
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            version_id.to_string(),
            None,
            Some(Default::default()),
        );
        assert_with(
            deleted,
            None,
            None,
            Some(EXPECTED_SEQUENCER_DELETED_TWO.to_string()),
            version_id.to_string(),
            None,
            Some(Default::default()),
        );
    }

    fn remove_version_ids(mut events: Events) -> Events {
        events
            .object_deleted
            .version_ids
            .iter_mut()
            .for_each(|version_id| *version_id = FlatS3EventMessage::default_version_id());
        events
            .object_created
            .version_ids
            .iter_mut()
            .for_each(|version_id| *version_id = FlatS3EventMessage::default_version_id());

        events
    }

    fn replace_sequencers(mut events: Events, sequencer: Option<String>) -> Events {
        events
            .object_deleted
            .sequencers
            .iter_mut()
            .for_each(|replace_sequencer| replace_sequencer.clone_from(&sequencer));
        events
            .object_created
            .sequencers
            .iter_mut()
            .for_each(|replace_sequencer| replace_sequencer.clone_from(&sequencer));

        events
    }

    pub(crate) async fn fetch_results<'a>(ingester: &'a Ingester<'a>) -> (Vec<PgRow>, Vec<PgRow>) {
        (
            sqlx::query("select * from object")
                .fetch_all(ingester.client.pool())
                .await
                .unwrap(),
            sqlx::query("select * from s3_object")
                .fetch_all(ingester.client.pool())
                .await
                .unwrap(),
        )
    }

    pub(crate) fn assert_created(s3_object_results: &PgRow) {
        assert_with(
            s3_object_results,
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            None,
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            None,
        )
    }

    pub(crate) fn assert_with(
        s3_object_results: &PgRow,
        size: Option<i64>,
        created_sequencer: Option<String>,
        deleted_sequencer: Option<String>,
        version_id: String,
        created_date: Option<DateTime<Utc>>,
        deleted_date: Option<DateTime<Utc>>,
    ) {
        assert_ne!(
            s3_object_results.get::<Uuid, _>("s3_object_id"),
            s3_object_results.get::<Uuid, _>("public_id")
        );
        assert_eq!("bucket", s3_object_results.get::<String, _>("bucket"));
        assert_eq!("key", s3_object_results.get::<String, _>("key"));
        assert_eq!(version_id, s3_object_results.get::<String, _>("version_id"));
        assert_eq!(
            created_sequencer,
            s3_object_results.get::<Option<String>, _>("created_sequencer")
        );
        assert_eq!(
            deleted_sequencer,
            s3_object_results.get::<Option<String>, _>("deleted_sequencer")
        );
        assert_eq!(size, s3_object_results.get::<Option<i64>, _>("size"));
        assert_eq!(
            Some(EXPECTED_SHA256.to_string()),
            s3_object_results.get::<Option<String>, _>("sha256")
        );
        assert_eq!(
            Some(EXPECTED_E_TAG.to_string()),
            s3_object_results.get::<Option<String>, _>("e_tag")
        );
        assert_eq!(
            DateTime::<Utc>::default(),
            s3_object_results.get::<DateTime<Utc>, _>("last_modified_date")
        );
        assert_eq!(
            created_date,
            s3_object_results.get::<Option<DateTime<Utc>>, _>("created_date")
        );
        assert_eq!(
            deleted_date,
            s3_object_results.get::<Option<DateTime<Utc>>, _>("deleted_date")
        );
    }

    fn update_test_events(mut events: Events) -> Events {
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

        update_last_modified(&mut events.object_created.last_modified_dates);
        update_storage_class(&mut events.object_created.storage_classes);
        update_sha256(&mut events.object_created.sha256s);

        update_last_modified(&mut events.object_deleted.last_modified_dates);
        update_storage_class(&mut events.object_deleted.storage_classes);
        update_sha256(&mut events.object_deleted.sha256s);

        events
    }

    pub(crate) fn test_events() -> Events {
        update_test_events(expected_events_simple())
    }

    pub(crate) fn test_ingester<'a>(pool: PgPool) -> Ingester<'a> {
        Ingester::new(Client::new(pool))
    }
}
