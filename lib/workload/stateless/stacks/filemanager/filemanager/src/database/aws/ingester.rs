//! This module handles logic associated with event ingestion.
//!

use sqlx::{query, PgConnection};
use tracing::debug;

use crate::database::aws::query::Query;
use crate::database::{Client, CredentialGenerator};
use crate::env::Config;
use crate::error::Error::ParseError;
use crate::error::{Error, Result};
use crate::events::aws::{FlatS3EventMessages, TransposedS3EventMessages};

/// The amount of padding to add to the sequencer when updating null values.
const SEQUENCER_PADDING_AMOUNT: usize = 30;

/// An ingester for S3 events.
#[derive(Debug)]
pub struct Ingester {
    pub(crate) client: Client,
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

    /// The default sequencer value, i.e. the lowest possible sequencer.
    pub(crate) fn default_sequencer() -> String {
        "0".repeat(SEQUENCER_PADDING_AMOUNT)
    }

    /// Increment the sequencer to a greater value. Sequencers are padding with enough zeros to
    /// ensure that the increment doesn't interfere with the ordering of AWS-native sequencer values.
    ///
    /// This increments the sequencer using the following logic:
    /// - If the sequencer is null, starting at `SEQUENCER_PADDING_AMOUNT` zeroes as the sequencer.
    /// - Then, adding a u64 value to the right side of the sequencer separated by `-` by:
    ///     1. Padding `SEQUENCER_PADDING_AMOUNT` zeroes right before adding the value if the
    ///        sequencer hasn't been padded before.
    ///     2. Incrementing the u64 value on the right if it has been padded.
    pub(crate) fn increment_sequencer(sequencer: Option<String>) -> Result<String> {
        // If no sequencer exists, start from the lowest possible value.
        let sequencer = sequencer.unwrap_or_else(Self::default_sequencer);

        if sequencer.len() > SEQUENCER_PADDING_AMOUNT {
            // Padding exists, increment the right side of the sequencer.
            let (left, right) = sequencer.rsplit_once("-").ok_or_else(|| {
                ParseError(format!(
                    "failed to parse sequencer for padding: {}",
                    sequencer
                ))
            })?;
            let decoded = hex::decode(right).map_err(|err| {
                ParseError(format!("failed to decode right padded sequencer: {}", err))
            })?;

            let mut number = u64::from_le_bytes(decoded.try_into().map_err(|err| {
                ParseError(format!(
                    "failed to convert sequencer to integer: {:x?}",
                    err
                ))
            })?);
            number += 1;

            let bytes = number.to_le_bytes();
            let encoded = hex::encode(bytes);

            Ok::<_, Error>(format!("{}-{}", left, encoded))
        } else {
            // Padding does not exist, start padding with the first value.
            let first = hex::encode(1_u64.to_le_bytes());

            Ok(format!(
                "{:0<SEQUENCER_PADDING_AMOUNT$}-{}",
                sequencer, first
            ))
        }
    }

    /// Convert null sequencers into proper values. This is required to ensure that events
    /// maintain the correct ordering between null and non-null sequencers. A new sequencer value
    /// is assigned for each null sequencer by incrementing the previous most recent sequencer.
    /// This assumes that the event with the null sequencer is the "most-current" event for the
    /// bucket, key and version_id.
    pub(crate) async fn resolve_null_sequencers(
        query: &Query,
        events: TransposedS3EventMessages,
        conn: &mut PgConnection,
    ) -> Result<TransposedS3EventMessages> {
        // Get the current state of records to find the most recent sequencer.
        let current = query
            .select_existing_by_bucket_key(conn, &events.buckets, &events.keys, &events.version_ids)
            .await?;

        let mut events = FlatS3EventMessages::from(events);
        // Then update the sequencers, proceeding in groups of keys, buckets and version_ids.
        for group in events.0.chunk_by_mut(|a, b| {
            a.key == b.key && a.bucket == b.bucket && a.version_id == b.version_id
        }) {
            let first = group.first();

            // Extract the current_sequencer from the database if it exists.
            let mut current_sequencer = current
                .0
                .iter()
                .find(|current| {
                    Some(current.bucket.as_str()) == first.map(|first| first.bucket.as_str())
                        && Some(current.key.as_str()) == first.map(|first| first.key.as_str())
                        && Some(current.version_id.as_str())
                            == first.map(|first| first.version_id.as_str())
                })
                .and_then(|current| current.sequencer.clone());

            // Update the sequencer for each consecutive event in the group based on the current.
            group.iter_mut().try_for_each(|event| {
                // If this event has an AWS-native sequencer, update it to the current and proceed.
                if event.sequencer.is_some() {
                    current_sequencer = event.sequencer.clone();
                    return Ok::<_, Error>(());
                }

                event.sequencer = Some(Self::increment_sequencer(current_sequencer.clone())?);
                current_sequencer = event.sequencer.clone();
                Ok::<_, Error>(())
            })?;
        }

        Ok(events.sort_and_dedup().into())
    }

    pub(crate) async fn ingest_query(
        events: &TransposedS3EventMessages,
        conn: &mut PgConnection,
    ) -> Result<()> {
        query(include_str!(
            "../../../../database/queries/ingester/aws/insert_s3_objects.sql"
        ))
        .bind(&events.s3_object_ids)
        .bind(&events.buckets)
        .bind(&events.keys)
        .bind(&events.event_times)
        .bind(&events.sizes)
        .bind(&events.sha256s)
        .bind(&events.last_modified_dates)
        .bind(&events.e_tags)
        .bind(&events.storage_classes)
        .bind(&events.version_ids)
        .bind(&events.sequencers)
        .bind(&events.is_delete_markers)
        .bind(&events.reasons)
        .bind(&events.archive_statuses)
        .bind(&events.event_types)
        .bind(&events.ingest_ids)
        .bind(&events.is_current_state)
        .bind(&events.attributes)
        .fetch_all(conn)
        .await?;

        Ok(())
    }

    /// Ingest the events into the database by calling the insert and update queries.
    pub async fn ingest_events(self, events: TransposedS3EventMessages) -> Result<()> {
        let mut tx = self.client().pool().begin().await?;

        let query = Query::new(self.client.clone());

        let mut events = events;
        // If there are any null sequencers, they should be converted to proper sequencers
        // first to ensure correct event ordering.
        if events
            .sequencers
            .iter()
            .any(|sequencer| sequencer.is_none())
        {
            events = Self::resolve_null_sequencers(&query, events, &mut tx).await?;
        }

        debug!(
            s3_object_ids = ?events.s3_object_ids,
            "inserting events into s3_object table"
        );
        Self::ingest_query(&events, &mut tx).await?;

        // Reset state for records which represent the new state.
        query
            .reset_current_state(
                &mut tx,
                &events.buckets,
                &events.keys,
                &events.version_ids,
                &events.sequencers,
            )
            .await?;

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
    use chrono::{DateTime, Utc};
    use itertools::Itertools;
    use sqlx::postgres::PgRow;
    use sqlx::{Executor, PgPool, Row};
    use tokio::time::Instant;
    use uuid::Uuid;

    use super::*;
    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::entities::sea_orm_active_enums::{ArchiveStatus, Reason};
    use crate::database::{Client, Ingest};
    use crate::events::aws::message::EventType::{Created, Deleted};
    use crate::events::aws::message::{default_version_id, EventType};
    use crate::events::aws::tests::{
        expected_events_simple, expected_events_simple_delete_marker, expected_flat_events_simple,
        EXPECTED_QUOTED_E_TAG, EXPECTED_SEQUENCER_CREATED_ONE, EXPECTED_SEQUENCER_CREATED_TWO,
        EXPECTED_SEQUENCER_CREATED_ZERO, EXPECTED_SEQUENCER_DELETED_ONE,
        EXPECTED_SEQUENCER_DELETED_TWO, EXPECTED_SHA256, EXPECTED_VERSION_ID,
    };
    use crate::events::aws::{
        FlatS3EventMessage, FlatS3EventMessages, StorageClass, TransposedS3EventMessages,
    };
    use crate::events::EventSourceType;
    use crate::events::EventSourceType::S3;
    use crate::uuid::UuidGenerator;

    #[test]
    fn sequencer_padding() {
        let sequencer = "123";
        let padded = Ingester::increment_sequencer(Some(sequencer.to_string())).unwrap();
        assert_eq!(
            padded,
            "123000000000000000000000000000-0100000000000000".to_string()
        );

        let pad_next = Ingester::increment_sequencer(Some(padded.to_string())).unwrap();
        assert_eq!(
            pad_next,
            "123000000000000000000000000000-0200000000000000".to_string()
        );

        assert!(*padded > *sequencer);
        assert!(*pad_next > *sequencer);
        assert!(pad_next > padded);

        let new_sequencer = "1245";

        assert!(*new_sequencer > *padded);
        assert!(*new_sequencer > *pad_next);

        let large_sequencer = "123400000000000000000000000000";
        let padded_large =
            Ingester::increment_sequencer(Some(large_sequencer.to_string())).unwrap();
        assert_eq!(
            padded_large,
            "123400000000000000000000000000-0100000000000000".to_string()
        );

        assert!(*padded_large > *large_sequencer);

        let too_large = "1234000000000000000000000000000";
        let result = Ingester::increment_sequencer(Some(too_large.to_string()));
        assert!(result.is_err());

        let no_sequencer = Ingester::increment_sequencer(None).unwrap();
        assert_eq!(
            no_sequencer,
            "000000000000000000000000000000-0100000000000000".to_string()
        );
        assert!(*sequencer > *no_sequencer);
        assert!(padded > no_sequencer);
        assert!(pad_next > no_sequencer);
        assert!(*too_large > *no_sequencer);
        assert!(*EXPECTED_SEQUENCER_CREATED_ONE > *no_sequencer);
        assert!(*EXPECTED_SEQUENCER_CREATED_TWO > *no_sequencer);
        assert!(*EXPECTED_SEQUENCER_CREATED_ZERO > *no_sequencer);
        assert!(*EXPECTED_SEQUENCER_DELETED_ONE > *no_sequencer);
        assert!(*EXPECTED_SEQUENCER_DELETED_TWO > *no_sequencer);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_padded(pool: PgPool) {
        let ingester = test_ingester(pool);
        let mut events_one = test_events(Some(Created));

        // Merge events into same ingestion.
        let flat_events: FlatS3EventMessages =
            replace_sequencers(test_events(None), None, None).into();
        flat_events
            .into_inner()
            .into_iter()
            .for_each(|event| events_one.push(event));

        ingester.ingest(S3(events_one)).await.unwrap();

        let s3_object_results = fetch_results_ordered(&ingester).await;

        assert_eq!(s3_object_results.len(), 3);
        assert_with(
            &s3_object_results[0],
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Created,
            false,
        );
        assert_with(
            &s3_object_results[1],
            Some(0),
            Some(format!(
                "{}000000000000-0100000000000000",
                EXPECTED_SEQUENCER_CREATED_ONE
            )),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Created,
            false,
        );
        assert_with(
            &s3_object_results[2],
            None,
            Some(format!(
                "{}000000000000-0200000000000000",
                EXPECTED_SEQUENCER_CREATED_ONE
            )),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Deleted,
            false,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_padded_separate(pool: PgPool) {
        let ingester = test_ingester(pool);
        let events_one = test_events(Some(Created));

        ingester.ingest(S3(events_one)).await.unwrap();

        let flat_events: FlatS3EventMessages =
            replace_sequencers(test_events(None), None, None).into();

        ingester.ingest(S3(flat_events.into())).await.unwrap();

        let s3_object_results = fetch_results_ordered(&ingester).await;

        assert_eq!(s3_object_results.len(), 3);
        assert_with(
            &s3_object_results[0],
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Created,
            false,
        );
        assert_with(
            &s3_object_results[1],
            Some(0),
            Some(format!(
                "{}000000000000-0100000000000000",
                EXPECTED_SEQUENCER_CREATED_ONE
            )),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Created,
            false,
        );
        assert_with(
            &s3_object_results[2],
            None,
            Some(format!(
                "{}000000000000-0200000000000000",
                EXPECTED_SEQUENCER_CREATED_ONE
            )),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Deleted,
            false,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_padded_separate_current_state(pool: PgPool) {
        let ingester = test_ingester(pool);
        let events_one = test_events(Some(Created));

        ingester.ingest(S3(events_one)).await.unwrap();

        let mut events = test_events(Some(Created));
        events.sequencers[0] = None;

        ingester.ingest(S3(events)).await.unwrap();

        let s3_object_results = fetch_results_ordered(&ingester).await;

        assert_eq!(s3_object_results.len(), 2);
        assert_with(
            &s3_object_results[0],
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Created,
            false,
        );
        assert_with(
            &s3_object_results[1],
            Some(0),
            Some(format!(
                "{}000000000000-0100000000000000",
                EXPECTED_SEQUENCER_CREATED_ONE
            )),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Created,
            true,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_padded_null_sequencer(pool: PgPool) {
        let ingester = test_ingester(pool.clone());
        let events_one = test_events(Some(Created));

        ingester.ingest(S3(events_one)).await.unwrap();

        let mut events = test_events(Some(Created));
        events.sequencers[0] = None;

        // Insert a null sequencer without changing it's value to simulate an old event.
        let mut tx = pool.begin().await.unwrap();
        Ingester::ingest_query(&events, &mut tx).await.unwrap();
        tx.commit().await.unwrap();

        let mut events = test_events(Some(Created));
        events.sequencers[0] = None;

        ingester.ingest(S3(events)).await.unwrap();

        let s3_object_results = fetch_results_ordered(&ingester).await;

        assert_eq!(s3_object_results.len(), 3);
        assert_with(
            &s3_object_results[0],
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Created,
            false,
        );
        assert_with(
            &s3_object_results[1],
            Some(0),
            Some(format!(
                "{}000000000000-0100000000000000",
                EXPECTED_SEQUENCER_CREATED_ONE
            )),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Created,
            true,
        );
        assert_with(
            &s3_object_results[2],
            Some(0),
            None,
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Created,
            false,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_padded_start_null_before(pool: PgPool) {
        let ingester = test_ingester(pool);

        let flat_events: FlatS3EventMessages =
            replace_sequencers(test_events(None), None, None).into();

        ingester.ingest(S3(flat_events.into())).await.unwrap();

        let events_one = test_events(Some(Created));
        ingester.ingest(S3(events_one)).await.unwrap();

        let s3_object_results = fetch_results_ordered(&ingester).await;

        assert_eq!(s3_object_results.len(), 3);
        assert_with(
            &s3_object_results[0],
            Some(0),
            Some("000000000000000000000000000000-0100000000000000".to_string()),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Created,
            false,
        );
        assert_with(
            &s3_object_results[1],
            None,
            Some("000000000000000000000000000000-0200000000000000".to_string()),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Deleted,
            false,
        );
        assert_with(
            &s3_object_results[2],
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Created,
            true,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_padded_separate_null(pool: PgPool) {
        let ingester = test_ingester(pool);

        let flat_events: FlatS3EventMessages =
            replace_sequencers(test_events(None), None, None).into();

        ingester.ingest(S3(flat_events.into())).await.unwrap();

        let s3_object_results = fetch_results_ordered(&ingester).await;

        assert_eq!(s3_object_results.len(), 2);
        assert_with(
            &s3_object_results[0],
            Some(0),
            Some("000000000000000000000000000000-0100000000000000".to_string()),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Created,
            false,
        );
        assert_with(
            &s3_object_results[1],
            None,
            Some("000000000000000000000000000000-0200000000000000".to_string()),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Deleted,
            false,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_created(pool: PgPool) {
        let events = test_events(Some(Created));

        let ingester = test_ingester(pool);
        ingester.ingest(S3(events)).await.unwrap();

        let s3_object_results = fetch_results(&ingester).await;

        assert_eq!(s3_object_results.len(), 1);
        assert!(s3_object_results[0]
            .get::<Option<Uuid>, _>("ingest_id")
            .is_some());
        assert_created(&s3_object_results[0]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_delete_marker(pool: PgPool) {
        let events: FlatS3EventMessages = FlatS3EventMessages::from(test_events_delete_marker());

        let ingester = test_ingester(pool);
        ingester.ingest(S3(events.into())).await.unwrap();

        let s3_object_results = fetch_results(&ingester).await;

        assert_eq!(s3_object_results.len(), 2);

        let message = expected_message(Some(0), EXPECTED_VERSION_ID.to_string(), true, Deleted)
            .with_is_current_state(false);
        assert_row(
            &s3_object_results[1],
            message,
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            Some(Default::default()),
        );

        let message = expected_message(None, EXPECTED_VERSION_ID.to_string(), false, Deleted)
            .with_is_current_state(false);
        assert_row(
            &s3_object_results[0],
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

        let s3_object_results = fetch_results(&ingester).await;

        assert_eq!(s3_object_results.len(), 1);
        assert!(s3_object_results[0]
            .get::<Option<Uuid>, _>("ingest_id")
            .is_some());
        assert_with(
            &s3_object_results[0],
            Some(i64::MAX),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Created,
            true,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_removed(pool: PgPool) {
        let events = test_events(None);

        let ingester = test_ingester(pool);
        ingester.ingest(S3(events)).await.unwrap();

        let s3_object_results = fetch_results(&ingester).await;

        println!("{:#?}", s3_object_results);
        assert_eq!(s3_object_results.len(), 2);
        assert_ingest_events(
            &s3_object_results[1],
            &s3_object_results[0],
            false,
            false,
            EXPECTED_VERSION_ID,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_duplicates(pool: PgPool) {
        let ingester = test_ingester(pool);
        ingester.ingest(S3(test_events(None))).await.unwrap();
        ingester.ingest(S3(test_events(None))).await.unwrap();

        let s3_object_results = fetch_results(&ingester).await;

        assert_eq!(s3_object_results.len(), 2);
        assert!(s3_object_results[0]
            .get::<Option<Uuid>, _>("ingest_id")
            .is_some());
        assert_eq!(
            1,
            s3_object_results[0].get::<i64, _>("number_duplicate_events")
        );
        assert_eq!(
            1,
            s3_object_results[1].get::<i64, _>("number_duplicate_events")
        );
        assert_ingest_events(
            &s3_object_results[1],
            &s3_object_results[0],
            false,
            false,
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
            Some(EXPECTED_SEQUENCER_CREATED_TWO.to_string()),
        )
        .into();
        flat_events
            .into_inner()
            .into_iter()
            .for_each(|event| events_one.push(event));

        ingester.ingest(S3(events_one)).await.unwrap();

        let s3_object_results = fetch_results(&ingester).await;

        assert_eq!(s3_object_results.len(), 3);
        assert_with(
            &s3_object_results[0],
            None,
            Some(EXPECTED_SEQUENCER_CREATED_TWO.to_string()),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Deleted,
            false,
        );
        assert_with(
            &s3_object_results[1],
            Some(0),
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Created,
            false,
        );
        assert_with(
            &s3_object_results[2],
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Created,
            false,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_duplicate_except_deleted_event_type(pool: PgPool) {
        let ingester = test_ingester(pool);
        let mut events_one = test_events(Some(Deleted));

        // Merge events into same ingestion.
        let flat_events: FlatS3EventMessages = replace_sequencers(
            test_events(None),
            Some(EXPECTED_SEQUENCER_CREATED_TWO.to_string()),
            Some(EXPECTED_SEQUENCER_DELETED_TWO.to_string()),
        )
        .into();
        flat_events
            .into_inner()
            .into_iter()
            .for_each(|event| events_one.push(event));

        ingester.ingest(S3(events_one)).await.unwrap();

        let s3_object_results = fetch_results(&ingester).await;

        assert_eq!(s3_object_results.len(), 3);
        assert_missing_created(
            &s3_object_results[2],
            &s3_object_results[0],
            EXPECTED_VERSION_ID,
        );
        assert_with(
            &s3_object_results[1],
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_TWO.to_string()),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Created,
            false,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_reorder(pool: PgPool) {
        let ingester = test_ingester(pool);

        // Deleted coming before created.
        ingester
            .ingest(S3(test_events(Some(Deleted))))
            .await
            .unwrap();
        ingester
            .ingest(S3(test_events(Some(Created))))
            .await
            .unwrap();

        let s3_object_results = fetch_results(&ingester).await;

        assert_eq!(s3_object_results.len(), 2);
        assert!(s3_object_results[0]
            .get::<Option<Uuid>, _>("ingest_id")
            .is_some());
        // Order should be different here.
        assert_ingest_events(
            &s3_object_results[1],
            &s3_object_results[0],
            false,
            false,
            EXPECTED_VERSION_ID,
        );

        let s3_object_results = fetch_results_ordered(&ingester).await;
        assert_eq!(s3_object_results.len(), 2);
        // However if querying by the sequencer, order should be correct
        assert_ingest_events(
            &s3_object_results[0],
            &s3_object_results[1],
            false,
            false,
            EXPECTED_VERSION_ID,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_without_version_id(pool: PgPool) {
        let ingester = test_ingester(pool);
        let events = remove_version_ids(test_events(None));

        ingester.ingest(S3(events)).await.unwrap();

        let s3_object_results = fetch_results(&ingester).await;

        assert_eq!(s3_object_results.len(), 2);
        assert_ingest_events(
            &s3_object_results[1],
            &s3_object_results[0],
            false,
            false,
            &default_version_id(),
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_duplicates_without_version_id(pool: PgPool) {
        let ingester = test_ingester(pool);
        ingester
            .ingest(S3(remove_version_ids(test_events(None))))
            .await
            .unwrap();
        ingester
            .ingest(S3(remove_version_ids(test_events(None))))
            .await
            .unwrap();

        let s3_object_results = fetch_results(&ingester).await;

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
            &s3_object_results[1],
            &s3_object_results[0],
            false,
            false,
            &default_version_id(),
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_duplicates_with_version_id(pool: PgPool) {
        let ingester = test_ingester(pool);
        ingester.ingest(S3(test_events(None))).await.unwrap();

        let event = expected_flat_events_simple().sort_and_dedup().into_inner();
        let mut event = event[0].clone();
        event.version_id = "version_id".to_string();
        event.sequencer = Some(EXPECTED_SEQUENCER_CREATED_TWO.to_string());

        let mut events = vec![event];
        events.extend(expected_flat_events_simple().sort_and_dedup().into_inner());

        let events = update_test_events(FlatS3EventMessages(events).into());

        ingester.ingest(S3(events)).await.unwrap();

        let s3_object_results = fetch_results(&ingester).await;

        println!("{:#?}", s3_object_results);
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
            &s3_object_results[2],
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Created,
            false,
        );
        assert_with(
            &s3_object_results[0],
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_TWO.to_string()),
            "version_id".to_string(),
            Some(Default::default()),
            Created,
            true,
        );
        assert_with(
            &s3_object_results[1],
            None,
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Deleted,
            false,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_missing_deleted(pool: PgPool) {
        let ingester = test_ingester(pool);

        let mut events_one = test_events(Some(Created));
        events_one.sequencers[0] = Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string());
        // New created event with a higher sequencer.
        let mut events_two = test_events(Some(Created));
        events_two.sequencers[0] = Some(EXPECTED_SEQUENCER_CREATED_TWO.to_string());

        ingester.ingest(S3(events_one)).await.unwrap();
        ingester.ingest(S3(events_two)).await.unwrap();

        let s3_object_results = fetch_results(&ingester).await;

        assert_eq!(s3_object_results.len(), 2);
        assert_missing_deleted(
            &s3_object_results[1],
            &s3_object_results[0],
            EXPECTED_VERSION_ID,
            false,
            true,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_missing_deleted_reorder(pool: PgPool) {
        let ingester = test_ingester(pool);

        let mut events_one = test_events(Some(Created));
        events_one.sequencers[0] = Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string());
        // New created event with a higher sequencer.
        let mut events_two = test_events(Some(Created));
        events_two.sequencers[0] = Some(EXPECTED_SEQUENCER_CREATED_TWO.to_string());

        // Re-order
        ingester.ingest(S3(events_two)).await.unwrap();
        ingester.ingest(S3(events_one)).await.unwrap();

        let s3_object_results = fetch_results_ordered(&ingester).await;

        assert_eq!(s3_object_results.len(), 2);
        assert_missing_deleted(
            &s3_object_results[0],
            &s3_object_results[1],
            EXPECTED_VERSION_ID,
            false,
            true,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_missing_created(pool: PgPool) {
        let ingester = test_ingester(pool);

        let mut events_one = test_events(Some(Deleted));
        events_one.sequencers[0] = Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string());
        // New created event with a higher sequencer.
        let mut events_two = test_events(Some(Deleted));
        events_two.sequencers[0] = Some(EXPECTED_SEQUENCER_DELETED_TWO.to_string());

        ingester.ingest(S3(events_one)).await.unwrap();
        ingester.ingest(S3(events_two)).await.unwrap();

        let s3_object_results = fetch_results(&ingester).await;

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

        let mut events_one = test_events(Some(Deleted));
        events_one.sequencers[0] = Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string());
        // New created event with a higher sequencer.
        let mut events_two = test_events(Some(Deleted));
        events_two.sequencers[0] = Some(EXPECTED_SEQUENCER_DELETED_TWO.to_string());

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
    async fn ingest_object_multiple_matching_rows_created(pool: PgPool) {
        let ingester = test_ingester(pool);

        let mut events_one = test_events(Some(Created));
        events_one.sequencers[0] = Some(EXPECTED_SEQUENCER_CREATED_ZERO.to_string());
        // New created event with a higher sequencer.
        let mut events_two = test_events(Some(Created));
        events_two.sequencers[0] = Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string());
        let mut events_three = test_events(Some(Deleted));
        events_three.sequencers[0] = Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string());

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
            false,
        );
        assert_ingest_events(
            &s3_object_results[1],
            &s3_object_results[2],
            false,
            false,
            EXPECTED_VERSION_ID,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_object_multiple_matching_rows_deleted(pool: PgPool) {
        let ingester = test_ingester(pool);

        let mut events_one = test_events(Some(Deleted));
        events_one.sequencers[0] = Some(EXPECTED_SEQUENCER_CREATED_TWO.to_string());
        // New created event with a higher sequencer.
        let mut events_two = test_events(Some(Deleted));
        events_two.sequencers[0] = Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string());
        let events_three = test_events(Some(Created));

        ingester.ingest(S3(events_one)).await.unwrap();
        ingester.ingest(S3(events_two)).await.unwrap();
        ingester.ingest(S3(events_three)).await.unwrap();

        let s3_object_results = fetch_results_ordered(&ingester).await;

        assert_eq!(s3_object_results.len(), 3);
        assert_with(
            &s3_object_results[2],
            None,
            Some(EXPECTED_SEQUENCER_CREATED_TWO.to_string()),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Deleted,
            false,
        );
        assert_ingest_events(
            &s3_object_results[0],
            &s3_object_results[1],
            false,
            false,
            EXPECTED_VERSION_ID,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_objects_reset_current_state(pool: PgPool) {
        let ingester = test_ingester(pool);

        let mut events_one = test_events(Some(Created));
        events_one.sequencers[0] = Some(EXPECTED_SEQUENCER_CREATED_TWO.to_string());
        let events_two = test_events(None);

        // Out of order.
        ingester.ingest(S3(events_one)).await.unwrap();
        ingester.ingest(S3(events_two)).await.unwrap();

        let s3_object_results = fetch_results_ordered(&ingester).await;

        assert_eq!(s3_object_results.len(), 3);
        assert_with(
            &s3_object_results[2],
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_TWO.to_string()),
            EXPECTED_VERSION_ID.to_string(),
            Some(Default::default()),
            Created,
            true,
        );
        assert_ingest_events(
            &s3_object_results[0],
            &s3_object_results[1],
            false,
            false,
            EXPECTED_VERSION_ID,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_objects_reset_current_state_versioned(pool: PgPool) {
        let ingester = test_ingester(pool);

        let mut events_one = test_events(Some(Created));
        events_one.sequencers[0] = Some(EXPECTED_SEQUENCER_CREATED_TWO.to_string());
        events_one.version_ids[0] = "2".to_string();
        // Previous version of the object.
        let mut events_two = test_events(Some(Created));
        events_two.version_ids[0] = "1".to_string();

        // Out of order.
        ingester.ingest(S3(events_one)).await.unwrap();
        ingester.ingest(S3(events_two)).await.unwrap();

        let s3_object_results = fetch_results_ordered(&ingester).await;

        assert_eq!(s3_object_results.len(), 2);
        assert_with(
            &s3_object_results[0],
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            "1".to_string(),
            Some(Default::default()),
            Created,
            false,
        );
        assert_with(
            &s3_object_results[1],
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_TWO.to_string()),
            "2".to_string(),
            Some(Default::default()),
            Created,
            true,
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
                .with_sequencer(Some("1".to_string()))
                .with_is_current_state(true),
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_default_version_id()
                .with_event_type(Deleted)
                .with_sequencer(Some("2".to_string()))
                .with_is_current_state(false),
            // Missing created event.
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_default_version_id()
                .with_event_type(Deleted)
                .with_sequencer(Some("3".to_string()))
                .with_is_current_state(false),
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_default_version_id()
                .with_event_type(Created)
                .with_sequencer(Some("4".to_string()))
                .with_is_current_state(true),
            // Missing deleted event.
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_default_version_id()
                .with_event_type(Created)
                .with_sequencer(Some("5".to_string()))
                .with_is_current_state(true),
            // Different key
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key1".to_string())
                .with_default_version_id()
                .with_event_type(Created)
                .with_sequencer(Some("1".to_string()))
                .with_is_current_state(true),
        ];

        let message = expected_message(None, default_version_id(), false, Created)
            .with_sha256(None)
            .with_e_tag(None)
            .with_last_modified_date(None)
            .with_reason(Reason::Unknown);
        // 720 permutations
        run_permutation_test(&pool, event_permutations, 6, |s3_object_results| {
            assert_row(
                &s3_object_results[0],
                message.clone().with_is_current_state(false),
                Some("1".to_string()),
                None,
            );
            assert_row(
                &s3_object_results[1],
                message
                    .clone()
                    .with_key("key1".to_string())
                    .with_is_current_state(true),
                Some("1".to_string()),
                None,
            );
            assert_row(
                &s3_object_results[2],
                message
                    .clone()
                    .with_event_type(Deleted)
                    .with_is_current_state(false),
                Some("2".to_string()),
                None,
            );
            assert_row(
                &s3_object_results[3],
                message
                    .clone()
                    .with_event_type(Deleted)
                    .with_is_current_state(false),
                Some("3".to_string()),
                None,
            );
            assert_row(
                &s3_object_results[4],
                message.clone().with_is_current_state(false),
                Some("4".to_string()),
                None,
            );
            assert_row(
                &s3_object_results[5],
                message.clone().with_is_current_state(true),
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
            .with_last_modified_date(None)
            .with_reason(Reason::Unknown);
        // 720 permutations
        run_permutation_test(&pool, event_permutations, 5, |s3_object_results| {
            assert_row(
                &s3_object_results[0],
                message.clone().with_is_current_state(false),
                Some("1".to_string()),
                None,
            );
            assert_row(
                &s3_object_results[1],
                message
                    .clone()
                    .with_version_id("version_id1".to_string())
                    .with_event_type(Deleted)
                    .with_is_current_state(false),
                Some("1".to_string()),
                None,
            );
            assert_row(
                &s3_object_results[2],
                message
                    .clone()
                    .with_event_type(Deleted)
                    .with_is_current_state(false),
                Some("2".to_string()),
                None,
            );
            assert_row(
                &s3_object_results[3],
                message.clone().with_is_current_state(false),
                Some("3".to_string()),
                None,
            );
            assert_row(
                &s3_object_results[4],
                message
                    .clone()
                    .with_event_type(Deleted)
                    .with_is_current_state(false),
                Some("4".to_string()),
                None,
            );
        })
        .await;
    }

    pub(crate) fn assert_ingest_events(
        created: &PgRow,
        deleted: &PgRow,
        created_state: bool,
        deleted_state: bool,
        version_id: &str,
    ) {
        assert_with(
            created,
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            version_id.to_string(),
            Some(Default::default()),
            Created,
            created_state,
        );
        assert_with(
            deleted,
            None,
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            version_id.to_string(),
            Some(Default::default()),
            Deleted,
            deleted_state,
        )
    }

    fn example_event_permutations() -> Vec<FlatS3EventMessage> {
        vec![
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_version_id("version_id".to_string())
                .with_event_type(Created)
                .with_sequencer(Some("1".to_string()))
                .with_is_current_state(true),
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_version_id("version_id".to_string())
                .with_event_type(Deleted)
                .with_sequencer(Some("2".to_string()))
                .with_is_current_state(false),
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_version_id("version_id".to_string())
                .with_event_type(Created)
                .with_sequencer(Some("3".to_string()))
                .with_is_current_state(true),
            // Duplicate
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_version_id("version_id".to_string())
                .with_event_type(Created)
                .with_sequencer(Some("3".to_string()))
                .with_is_current_state(true),
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_version_id("version_id".to_string())
                .with_event_type(Deleted)
                .with_sequencer(Some("4".to_string()))
                .with_is_current_state(false),
            // Different version id
            FlatS3EventMessage::new_with_generated_id()
                .with_bucket("bucket".to_string())
                .with_key("key".to_string())
                .with_version_id("version_id1".to_string())
                .with_event_type(Deleted)
                .with_sequencer(Some("1".to_string()))
                .with_is_current_state(false),
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
            pool.execute("truncate s3_object").await.unwrap();
        }

        println!(
            "permutation test took: {} seconds",
            now.elapsed().as_secs_f32()
        );
    }

    fn assert_missing_deleted(
        created: &PgRow,
        deleted: &PgRow,
        version_id: &str,
        created_state: bool,
        deleted_state: bool,
    ) {
        assert_with(
            created,
            Some(0),
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            version_id.to_string(),
            Some(Default::default()),
            Created,
            created_state,
        );
        assert_with(
            deleted,
            Some(0),
            Some(EXPECTED_SEQUENCER_CREATED_TWO.to_string()),
            version_id.to_string(),
            Some(Default::default()),
            Created,
            deleted_state,
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
            false,
        );
        assert_with(
            created,
            None,
            Some(EXPECTED_SEQUENCER_DELETED_TWO.to_string()),
            version_id.to_string(),
            Some(Default::default()),
            Deleted,
            false,
        );
    }

    pub(crate) fn remove_version_ids(
        mut events: TransposedS3EventMessages,
    ) -> TransposedS3EventMessages {
        events
            .version_ids
            .iter_mut()
            .for_each(|version_id| *version_id = default_version_id());

        events
    }

    pub(crate) fn replace_sequencers(
        mut events: TransposedS3EventMessages,
        sequencer_one: Option<String>,
        sequencer_two: Option<String>,
    ) -> TransposedS3EventMessages {
        events.sequencers[0] = sequencer_one;
        events.sequencers[1] = sequencer_two;

        events
    }

    pub(crate) async fn fetch_results(client: &Client) -> Vec<PgRow> {
        sqlx::query("select * from s3_object")
            .fetch_all(client.pool())
            .await
            .unwrap()
    }

    pub(crate) async fn fetch_results_ordered(client: &Client) -> Vec<PgRow> {
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
            true,
        )
    }

    pub(crate) fn assert_row(
        s3_object_results: &PgRow,
        message: FlatS3EventMessage,
        sequencer: Option<String>,
        event_time: Option<DateTime<Utc>>,
    ) {
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
            event_time,
            s3_object_results.get::<Option<DateTime<Utc>>, _>("event_time")
        );
        assert_eq!(
            message.is_delete_marker,
            s3_object_results.get::<bool, _>("is_delete_marker")
        );
        assert_eq!(message.reason, s3_object_results.get::<Reason, _>("reason"));
        assert_eq!(
            message.archive_status,
            s3_object_results.get::<Option<ArchiveStatus>, _>("archive_status")
        );
        assert_eq!(
            message.is_current_state,
            s3_object_results.get::<bool, _>("is_current_state")
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
            .with_e_tag(Some(EXPECTED_QUOTED_E_TAG.to_string()))
            .with_sha256(Some(EXPECTED_SHA256.to_string()))
            .with_is_delete_marker(is_delete_marker)
            .with_reason(match event_type {
                Created => Reason::CreatedPut,
                Deleted => Reason::Deleted,
                _ => Reason::Unknown,
            })
            .with_event_type(event_type)
    }

    pub(crate) fn assert_with(
        s3_object_results: &PgRow,
        size: Option<i64>,
        sequencer: Option<String>,
        version_id: String,
        event_time: Option<DateTime<Utc>>,
        event_type: EventType,
        is_current_state: bool,
    ) {
        let message = expected_message(size, version_id, false, event_type)
            .with_is_current_state(is_current_state);

        assert_row(s3_object_results, message, sequencer, event_time);
    }

    pub(crate) fn update_test_events(
        mut events: TransposedS3EventMessages,
    ) -> TransposedS3EventMessages {
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
        let update_ingest_ids = |ingest_ids: &mut Vec<Option<Uuid>>| {
            ingest_ids.iter_mut().for_each(|ingest_id| {
                *ingest_id = Some(UuidGenerator::generate());
            });
        };

        update_last_modified(&mut events.last_modified_dates);
        update_storage_class(&mut events.storage_classes);
        update_sha256(&mut events.sha256s);
        update_ingest_ids(&mut events.ingest_ids);

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
