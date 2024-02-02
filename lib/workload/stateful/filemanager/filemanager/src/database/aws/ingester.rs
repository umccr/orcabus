use async_trait::async_trait;
use chrono::{DateTime, Utc};
use sqlx::{query_file, query_file_as};
use tracing::{debug, trace};

use crate::database::{Client, Ingest};
use crate::error::Result;
use crate::events::aws::EventType;
use crate::events::aws::{Events, TransposedS3EventMessages};
use crate::events::aws::{FlatS3EventMessage, FlatS3EventMessages, StorageClass};
use crate::events::EventSourceType;
use uuid::Uuid;

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
            mut object_created,
            object_deleted: mut object_removed,
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
            &object_created.version_ids as &[Option<String>],
            &object_created.sequencers as &[Option<String>],
            &object_created.event_times as &[Option<DateTime<Utc>>],
        )
        .fetch_all(&mut *tx)
        .await?;

        if !updated.is_empty() {
            // Now, events with a sequencer value need to be reprocessed.
            let mut flat_object_created = FlatS3EventMessages::from(object_created).into_inner();
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
                        false
                    } else {
                        *object = reprocess;
                        true
                    }
                } else {
                    true
                }
            });

            object_created = TransposedS3EventMessages::from(
                FlatS3EventMessages(flat_object_created).sort_and_dedup(),
            );
        }

        let object_ids = vec![Uuid::new_v4(); object_created.s3_object_ids.len()];
        let mut inserted = query_file!(
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

        let (object_ids, _): (Vec<_>, Vec<_>) = object_ids
            .into_iter()
            .rev()
            .zip(object_created.sizes.into_iter().rev())
            .flat_map(|(object_id, size)| {
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
                Some((object_id, size))
            })
            .unzip();

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
        let mut tx = self.client().pool().begin().await?;

        trace!(object_removed = ?object_removed, "ingesting object removed events");

        // First, try and update existing events to remove any un-ordered events.
        let updated = query_file_as!(
            FlatS3EventMessage,
            "../database/queries/ingester/aws/update_reordered_for_deleted.sql",
            &object_removed.s3_object_ids,
            &object_removed.buckets,
            &object_removed.keys,
            &object_removed.version_ids as &[Option<String>],
            &object_removed.sequencers as &[Option<String>],
            &object_removed.event_times as &[Option<DateTime<Utc>>],
        )
        .fetch_all(&mut *tx)
        .await?;

        if !updated.is_empty() {
            // Now, events with a sequencer value need to be reprocessed.
            let mut flat_object_removed = FlatS3EventMessages::from(object_removed).into_inner();
            let mut reprocess = FlatS3EventMessages(updated).into_inner();

            flat_object_removed.retain_mut(|object| {
                // If the sequencer is null, then we remove this object has it has already been consumed. Otherwise,
                // we keep it, and potentially replace an existing object.
                if let Some(pos) = reprocess
                    .iter()
                    .position(|reprocess| reprocess.s3_object_id == object.s3_object_id)
                {
                    let reprocess = reprocess.remove(pos);
                    if reprocess.sequencer.is_none() {
                        false
                    } else {
                        *object = reprocess;
                        true
                    }
                } else {
                    true
                }
            });

            object_removed = TransposedS3EventMessages::from(
                FlatS3EventMessages(flat_object_removed).sort_and_dedup(),
            );
        }

        let object_ids = vec![Uuid::new_v4(); object_removed.s3_object_ids.len()];
        let mut inserted = query_file!(
            "../database/queries/ingester/aws/insert_s3_deleted_objects.sql",
            &object_removed.s3_object_ids,
            &object_ids,
            &object_removed.buckets,
            &object_removed.keys,
            &object_removed.event_times as &[Option<DateTime<Utc>>],
            &object_removed.sizes as &[Option<i32>],
            &vec![None; object_removed.s3_object_ids.len()] as &[Option<String>],
            &object_removed.last_modified_dates as &[Option<DateTime<Utc>>],
            &object_removed.e_tags as &[Option<String>],
            &object_removed.storage_classes as &[Option<StorageClass>],
            &object_removed.version_ids as &[Option<String>],
            &object_removed.sequencers as &[Option<String>],
            // Fill this with 1 reorder, because if we get here then this must be a reordered event.
            &vec![1; object_removed.s3_object_ids.len()]
        )
        .fetch_all(&mut *tx)
        .await?;

        let (object_ids, _): (Vec<_>, Vec<_>) = object_ids
            .into_iter()
            .rev()
            .zip(object_removed.sizes.into_iter().rev())
            .flat_map(|(object_id, size)| {
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
                Some((object_id, size))
            })
            .unzip();

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
    use crate::database::aws::ingester::Ingester;
    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::{Client, Ingest};
    use crate::events::aws::tests::{
        expected_events_simple, expected_flat_events_simple, EXPECTED_E_TAG,
        EXPECTED_SEQUENCER_CREATED_ONE, EXPECTED_VERSION_ID,
    };
    use crate::events::aws::{Events, FlatS3EventMessages, StorageClass};
    use crate::events::EventSourceType;
    use chrono::{DateTime, Utc};
    use sqlx::postgres::PgRow;
    use sqlx::{PgPool, Row};
    use std::ops::Add;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_created(pool: PgPool) {
        let mut events = test_events();
        events.object_deleted = Default::default();

        let ingester = test_ingester(pool);
        ingester.ingest_events(events).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 1);
        assert_eq!(s3_object_results.len(), 1);
        assert_created(&object_results[0], &s3_object_results[0]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_removed(pool: PgPool) {
        let events = test_events();

        let ingester = test_ingester(pool);
        ingester.ingest_events(events).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 1);
        assert_eq!(s3_object_results.len(), 1);
        assert_deleted_with(&object_results[0], &s3_object_results[0], Some(0));
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest(pool: PgPool) {
        let events = test_events();

        let ingester = test_ingester(pool);
        ingester.ingest(EventSourceType::S3(events)).await.unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 1);
        assert_eq!(s3_object_results.len(), 1);
        assert_deleted_with(&object_results[0], &s3_object_results[0], Some(0));
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
        assert_deleted_with(&object_results[0], &s3_object_results[0], Some(0));
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
        assert_deleted_with(&object_results[0], &s3_object_results[0], None);
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
        assert_deleted_with(&object_results[1], &s3_object_results[1], Some(0));
        assert_created_with(
            &object_results[0],
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
        assert_deleted_with(&object_results[1], &s3_object_results[1], Some(0));
        assert_created_with(
            &object_results[0],
            &s3_object_results[0],
            "version_id",
            EXPECTED_SEQUENCER_CREATED_ONE,
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
        object_results: &PgRow,
        s3_object_results: &PgRow,
        expected_version_id: &str,
        expected_sequencer: &str,
    ) {
        assert_eq!("bucket", s3_object_results.get::<String, _>("bucket"));
        assert_eq!("key", s3_object_results.get::<String, _>("key"));
        assert_eq!(0, object_results.get::<i32, _>("size"));
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

    pub(crate) fn assert_created(object_results: &PgRow, s3_object_results: &PgRow) {
        assert_created_with(
            object_results,
            s3_object_results,
            EXPECTED_VERSION_ID,
            EXPECTED_SEQUENCER_CREATED_ONE,
        )
    }

    pub(crate) fn assert_deleted_with(
        object_results: &PgRow,
        s3_object_results: &PgRow,
        size: Option<i32>,
    ) {
        assert_eq!("bucket", s3_object_results.get::<String, _>("bucket"));
        assert_eq!("key", s3_object_results.get::<String, _>("key"));
        assert_eq!(
            EXPECTED_VERSION_ID,
            s3_object_results.get::<String, _>("version_id")
        );
        assert_eq!(size, object_results.get::<Option<i32>, _>("size"));
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
