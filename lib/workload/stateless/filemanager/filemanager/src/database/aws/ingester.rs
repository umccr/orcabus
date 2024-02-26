use async_trait::async_trait;
use chrono::{DateTime, Utc};
use sqlx::{query_file, query_file_as};
use tracing::{debug, trace};
use uuid::Uuid;

use crate::database::{Client, Ingest};
use crate::error::Result;
use crate::events::aws::message::EventType;
use crate::events::aws::{Events, TransposedS3EventMessages};
use crate::events::aws::{FlatS3EventMessage, FlatS3EventMessages, StorageClass};
use crate::events::EventSourceType;

/// An ingester for S3 events.
#[derive(Debug)]
pub struct Ingester {
    client: Client,
}

/// The type representing an insert query.
#[derive(Debug)]
struct Insert {
    object_id: Uuid,
    number_duplicate_events: i32,
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
            &object_created.sizes as &[Option<i32>],
            &vec![None; object_created.s3_object_ids.len()] as &[Option<String>],
            &object_created.last_modified_dates as &[Option<DateTime<Utc>>],
            &object_created.e_tags as &[Option<String>],
            &object_created.storage_classes as &[Option<StorageClass>],
            &object_created.version_ids as &[Option<String>],
            &object_created.sequencers as &[Option<String>]
        )
        .fetch_all(&mut *tx)
        .await?;

        let object_created = Self::reprocess_updated(object_created, updated);
        let object_ids = vec![Uuid::new_v4(); object_created.s3_object_ids.len()];

        let mut inserted = query_file_as!(
            Insert,
            "../database/queries/ingester/aws/insert_s3_created_objects.sql",
            &object_created.s3_object_ids,
            &object_ids,
            &object_created.buckets,
            &object_created.keys,
            &object_created.event_times as &[Option<DateTime<Utc>>],
            &object_created.sizes as &[Option<i32>],
            &vec![None; object_created.s3_object_ids.len()] as &[Option<String>],
            &object_created.last_modified_dates as &[Option<DateTime<Utc>>],
            &object_created.e_tags as &[Option<String>],
            &object_created.storage_classes as &[Option<StorageClass>],
            &object_created.version_ids as &[Option<String>],
            &object_created.sequencers as &[Option<String>]
        )
        .fetch_all(&mut *tx)
        .await?;

        let object_ids = Self::reprocess_inserts(object_ids, &mut inserted);

        // Insert only the non duplicate events.
        if !object_ids.is_empty() {
            debug!(count = object_ids.len(), "inserting objects");

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
            &object_deleted.version_ids as &[Option<String>],
            &object_deleted.sequencers as &[Option<String>],
        )
        .fetch_all(&mut *tx)
        .await?;

        let object_deleted = Self::reprocess_updated(object_deleted, updated);
        let object_ids = vec![Uuid::new_v4(); object_deleted.s3_object_ids.len()];

        let mut inserted = query_file_as!(
            Insert,
            "../database/queries/ingester/aws/insert_s3_deleted_objects.sql",
            &object_deleted.s3_object_ids,
            &object_ids,
            &object_deleted.buckets,
            &object_deleted.keys,
            &object_deleted.event_times as &[Option<DateTime<Utc>>],
            &object_deleted.sizes as &[Option<i32>],
            &vec![None; object_deleted.s3_object_ids.len()] as &[Option<String>],
            &object_deleted.last_modified_dates as &[Option<DateTime<Utc>>],
            &object_deleted.e_tags as &[Option<String>],
            &object_deleted.storage_classes as &[Option<StorageClass>],
            &object_deleted.version_ids as &[Option<String>],
            &object_deleted.sequencers as &[Option<String>],
            // Fill this with 1 reorder, because if we get here then this must be a reordered event.
            &vec![1; object_deleted.s3_object_ids.len()]
        )
        .fetch_all(&mut *tx)
        .await?;

        let object_ids = Self::reprocess_inserts(object_ids, &mut inserted);

        // Insert only the non duplicate events.
        if !object_ids.is_empty() {
            debug!(count = object_ids.len(), "inserting objects");

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
impl Ingest for Ingester {
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
    use sqlx::{PgPool, Row};
    use tokio::time::Instant;

    use crate::database::aws::ingester::Ingester;
    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::{Client, Ingest};
    use crate::events::aws::message::EventType::{Created, Deleted};
    use crate::events::aws::tests::{
        expected_events_simple, expected_flat_events_simple, EXPECTED_E_TAG,
        EXPECTED_SEQUENCER_CREATED_ONE, EXPECTED_VERSION_ID,
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
    async fn ingest_object_removed(pool: PgPool) {
        let events = test_events();

        let ingester = test_ingester(pool);
        ingester.ingest_events(events).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 1);
        assert_eq!(s3_object_results.len(), 1);
        assert_deleted_with(&s3_object_results[0], Some(0));
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest(pool: PgPool) {
        let events = test_events();

        let ingester = test_ingester(pool);
        ingester.ingest(EventSourceType::S3(events)).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 1);
        assert_eq!(s3_object_results.len(), 1);
        assert_deleted_with(&s3_object_results[0], Some(0));
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
            s3_object_results[0].get::<i32, _>("number_duplicate_events")
        );
        assert_deleted_with(&s3_object_results[0], Some(0));
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_reorder(pool: PgPool) {
        let ingester = test_ingester(pool);
        let events = test_events();
        // Deleted coming before created.
        ingester
            .ingest(EventSourceType::S3(Events {
                object_created: Default::default(),
                object_deleted: events.object_deleted,
                other: Default::default(),
            }))
            .await
            .unwrap();
        ingester
            .ingest(EventSourceType::S3(Events {
                object_created: events.object_created,
                object_deleted: Default::default(),
                other: Default::default(),
            }))
            .await
            .unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 1);
        assert_eq!(s3_object_results.len(), 1);
        assert_eq!(2, s3_object_results[0].get::<i32, _>("number_reordered"));
        assert_deleted_with(&s3_object_results[0], Some(0));
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
            s3_object_results[0].get::<i32, _>("number_duplicate_events")
        );
        assert_eq!(0, s3_object_results[0].get::<i32, _>("number_reordered"));
        assert_eq!(
            1,
            s3_object_results[1].get::<i32, _>("number_duplicate_events")
        );
        assert_eq!(1, s3_object_results[1].get::<i32, _>("number_reordered"));
        assert_deleted_with(&s3_object_results[1], Some(0));
        assert_created_with(
            &s3_object_results[0],
            EXPECTED_VERSION_ID,
            EXPECTED_SEQUENCER_CREATED_ONE,
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
        event.version_id = Some("version_id".to_string());

        let mut events = vec![event];
        events.extend(expected_flat_events_simple().sort_and_dedup().into_inner());

        let events = update_test_events(FlatS3EventMessages(events).into());

        ingester.ingest(EventSourceType::S3(events)).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 2);
        assert_eq!(s3_object_results.len(), 2);
        assert_eq!(
            0,
            s3_object_results[0].get::<i32, _>("number_duplicate_events")
        );
        assert_eq!(0, s3_object_results[0].get::<i32, _>("number_reordered"));
        assert_eq!(
            2,
            s3_object_results[1].get::<i32, _>("number_duplicate_events")
        );
        assert_eq!(0, s3_object_results[1].get::<i32, _>("number_reordered"));
        assert_deleted_with(&s3_object_results[1], Some(0));
        assert_created_with(
            &s3_object_results[0],
            "version_id",
            EXPECTED_SEQUENCER_CREATED_ONE,
        );
    }

    #[ignore]
    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_permutations(pool: PgPool) {
        // This primarily tests out of order and duplicate event ingestion, however it could also function
        // as a performance test.
        let event_permutations = vec![
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_version_id(Some("version_id".to_string()))
                .with_event_type(Created)
                .with_sequencer(Some("1".to_string())),
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_version_id(Some("version_id".to_string()))
                .with_event_type(Deleted)
                .with_sequencer(Some("2".to_string())),
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_version_id(Some("version_id".to_string()))
                .with_event_type(Created)
                .with_sequencer(Some("3".to_string())),
            // Duplicate
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_version_id(Some("version_id".to_string()))
                .with_event_type(Created)
                .with_sequencer(Some("3".to_string())),
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_version_id(Some("version_id".to_string()))
                .with_event_type(Deleted)
                .with_sequencer(Some("4".to_string())),
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_version_id(Some("version_id".to_string()))
                .with_event_type(Created)
                .with_sequencer(Some("5".to_string())),
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_version_id(Some("version_id".to_string()))
                .with_event_type(Deleted)
                .with_sequencer(Some("6".to_string())),
            // Different version id
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_version_id(Some("version_id1".to_string()))
                .with_event_type(Deleted)
                .with_sequencer(Some("1".to_string())),
        ];

        let now = Instant::now();

        let length = event_permutations.len();
        // 40320 permutations
        for events in event_permutations.into_iter().permutations(length) {
            let ingester = test_ingester(pool.clone());

            ingester
                .ingest(EventSourceType::S3(
                    // Okay to dedup here as the Lambda function would be doing this anyway.
                    FlatS3EventMessages(events[0..2].to_vec()).dedup().into(),
                ))
                .await
                .unwrap();
            ingester
                .ingest(EventSourceType::S3(
                    FlatS3EventMessages(vec![events[2].clone()]).into(),
                ))
                .await
                .unwrap();
            ingester
                .ingest(EventSourceType::S3(
                    FlatS3EventMessages(vec![events[3].clone()]).into(),
                ))
                .await
                .unwrap();
            ingester
                .ingest(EventSourceType::S3(
                    FlatS3EventMessages(vec![events[4].clone()]).into(),
                ))
                .await
                .unwrap();
            ingester
                .ingest(EventSourceType::S3(
                    FlatS3EventMessages(events[5..].to_vec()).dedup().into(),
                ))
                .await
                .unwrap();

            let (object_results, s3_object_results) = fetch_results(&ingester).await;

            assert_eq!(object_results.len(), 4);
            assert_eq!(s3_object_results.len(), 4);

            s3_object_results
                .iter()
                .find(|object| {
                    object.get::<String, _>("key") == "key"
                        && object.get::<String, _>("bucket") == "bucket"
                        && object.get::<Option<String>, _>("version_id")
                            == Some("version_id".to_string())
                        && object.get::<Option<String>, _>("created_sequencer")
                            == Some("1".to_string())
                        && object.get::<Option<String>, _>("deleted_sequencer")
                            == Some("2".to_string())
                })
                .unwrap();
            s3_object_results
                .iter()
                .find(|object| {
                    object.get::<String, _>("key") == "key"
                        && object.get::<String, _>("bucket") == "bucket"
                        && object.get::<Option<String>, _>("version_id")
                            == Some("version_id".to_string())
                        && object.get::<Option<String>, _>("created_sequencer")
                            == Some("3".to_string())
                        && object.get::<Option<String>, _>("deleted_sequencer")
                            == Some("4".to_string())
                })
                .unwrap();
            s3_object_results
                .iter()
                .find(|object| {
                    object.get::<String, _>("key") == "key"
                        && object.get::<String, _>("bucket") == "bucket"
                        && object.get::<Option<String>, _>("version_id")
                            == Some("version_id".to_string())
                        && object.get::<Option<String>, _>("created_sequencer")
                            == Some("5".to_string())
                        && object.get::<Option<String>, _>("deleted_sequencer")
                            == Some("6".to_string())
                })
                .unwrap();
            s3_object_results
                .iter()
                .find(|object| {
                    object.get::<String, _>("key") == "key"
                        && object.get::<String, _>("bucket") == "bucket"
                        && object.get::<Option<String>, _>("version_id")
                            == Some("version_id1".to_string())
                        && object
                            .get::<Option<String>, _>("created_sequencer")
                            .is_none()
                        && object.get::<Option<String>, _>("deleted_sequencer")
                            == Some("1".to_string())
                })
                .unwrap();
        }

        println!(
            "permutation test took: {} seconds",
            now.elapsed().as_secs_f32()
        );
    }

    pub(crate) async fn fetch_results(ingester: &Ingester) -> (Vec<PgRow>, Vec<PgRow>) {
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

    pub(crate) fn assert_created_with(
        s3_object_results: &PgRow,
        expected_version_id: &str,
        expected_sequencer: &str,
    ) {
        assert_eq!("bucket", s3_object_results.get::<String, _>("bucket"));
        assert_eq!("key", s3_object_results.get::<String, _>("key"));
        assert_eq!(0, s3_object_results.get::<i32, _>("size"));
        assert_eq!(EXPECTED_E_TAG, s3_object_results.get::<String, _>("e_tag"));
        assert_eq!(
            expected_version_id,
            s3_object_results.get::<String, _>("version_id")
        );
        assert_eq!(
            expected_sequencer,
            s3_object_results.get::<String, _>("created_sequencer")
        );
        assert_eq!(
            DateTime::<Utc>::default(),
            s3_object_results.get::<DateTime<Utc>, _>("created_date")
        );
        assert_eq!(
            DateTime::<Utc>::default(),
            s3_object_results.get::<DateTime<Utc>, _>("last_modified_date")
        );
    }

    pub(crate) fn assert_created(s3_object_results: &PgRow) {
        assert_created_with(
            s3_object_results,
            EXPECTED_VERSION_ID,
            EXPECTED_SEQUENCER_CREATED_ONE,
        )
    }

    pub(crate) fn assert_deleted_with(s3_object_results: &PgRow, size: Option<i32>) {
        assert_eq!("bucket", s3_object_results.get::<String, _>("bucket"));
        assert_eq!("key", s3_object_results.get::<String, _>("key"));
        assert_eq!(
            EXPECTED_VERSION_ID,
            s3_object_results.get::<String, _>("version_id")
        );
        assert_eq!(size, s3_object_results.get::<Option<i32>, _>("size"));
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

        update_last_modified(&mut events.object_created.last_modified_dates);
        update_storage_class(&mut events.object_created.storage_classes);

        update_last_modified(&mut events.object_deleted.last_modified_dates);
        update_storage_class(&mut events.object_deleted.storage_classes);

        events
    }

    pub(crate) fn test_events() -> Events {
        update_test_events(expected_events_simple())
    }

    pub(crate) fn test_ingester(pool: PgPool) -> Ingester {
        Ingester::new(Client::new(pool))
    }
}
