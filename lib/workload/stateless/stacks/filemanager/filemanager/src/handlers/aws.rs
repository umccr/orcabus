//! Event handlers for AWS, such as Lambda event handlers.
//!

use std::collections::HashSet;

use aws_lambda_events::sqs::SqsEvent;
use itertools::Itertools;
use sea_orm::DatabaseConnection;
use tracing::{debug, trace};

use crate::clients::aws::s3::Client as S3Client;
use crate::clients::aws::sqs::Client as SQSClient;
use crate::database::aws::credentials::IamGeneratorBuilder;
use crate::database::aws::query::Query;
use crate::database::{Client, Ingest};
use crate::env::Config as EnvConfig;
use crate::error::Error::ConfigError;
use crate::error::Result;
use crate::events::aws::collecter::CollecterBuilder;
use crate::events::aws::inventory::{DiffMessages, Inventory, Manifest};
use crate::events::aws::message::EventType::Created;
use crate::events::aws::{FlatS3EventMessages, TransposedS3EventMessages};
use crate::events::{Collect, EventSourceType};

/// Handle SQS events by manually calling the SQS receive function. This is meant
/// to be run through something like API gateway to manually invoke ingestion. Returns
/// the number of records processed.
pub async fn receive_and_ingest<'a>(
    s3_client: S3Client,
    sqs_client: SQSClient,
    sqs_url: Option<impl Into<String>>,
    database_client: &'a Client,
    env_config: &'a EnvConfig,
) -> Result<usize> {
    let (events, n_records) = CollecterBuilder::default()
        .with_s3_client(s3_client)
        .with_sqs_client(sqs_client)
        .set_sqs_url(sqs_url)
        .build_receive(env_config, database_client)
        .await?
        .collect()
        .await?
        .into_inner();

    database_client.ingest(events).await?;
    Ok(n_records)
}

/// Handle SQS events that go through an SqsEvent.
pub async fn ingest_event(
    event: SqsEvent,
    s3_client: S3Client,
    database_client: Client,
    env_config: &EnvConfig,
) -> Result<Client> {
    trace!("received event: {:?}", event);

    let events = event
        .records
        .into_iter()
        .filter_map(|event| {
            event.body.map(|body| {
                let body: Option<FlatS3EventMessages> = serde_json::from_str(&body)?;
                Ok(body.unwrap_or_default())
            })
        })
        .collect::<Result<Vec<_>>>()?
        .into();

    trace!("flattened events: {:?}", events);

    let events = CollecterBuilder::default()
        .with_s3_client(s3_client)
        .build(events, env_config, &database_client)
        .await
        .collect()
        .await?
        .into_inner()
        .0;

    trace!("ingesting events: {:?}", events);

    database_client.ingest(events).await?;
    Ok(database_client)
}

/// Handle an S3 inventory for ingestion.
pub async fn ingest_s3_inventory(
    s3_client: S3Client,
    database_client: Client,
    bucket: Option<String>,
    key: Option<String>,
    manifest: Option<Manifest>,
    env_config: &EnvConfig,
) -> Result<Client> {
    if env_config.paired_ingest_mode() {
        return Err(ConfigError(
            "paired ingest mode is not supported for S3 inventory".to_string(),
        ));
    }

    let inventory = Inventory::new(s3_client);

    let records = if let Some(manifest) = manifest {
        inventory.parse_manifest(manifest).await?
    } else if let (Some(bucket), Some(key)) = (bucket, key) {
        inventory.parse_manifest_key(key, bucket).await?
    } else {
        return Err(ConfigError(
            "either a manifest or bucket and key option needs to be specified".to_string(),
        ));
    };
    trace!("records extracted from inventory: {:#?}", records);

    let transposed_events: TransposedS3EventMessages =
        FlatS3EventMessages::from(records).sort_and_dedup().into();

    let query = Query::new(database_client.clone());

    let mut tx = query.transaction().await?;
    let database_records = query
        .select_existing_by_bucket_key(
            &mut tx,
            transposed_events.buckets.as_slice(),
            transposed_events.keys.as_slice(),
            transposed_events.version_ids.as_slice(),
        )
        .await?;
    tx.commit().await?;

    // Get only the current created state of records.
    let database_records = FlatS3EventMessages(
        database_records
            .0
            .into_iter()
            .filter(|record| record.event_type == Created)
            .collect(),
    );

    // Some back and forth between transposed vs not transposed events. Potential optimization
    // could involve using ndarray + slicing, with an enum representing the fields of the struct.
    let transposed_events: HashSet<DiffMessages> = HashSet::from_iter(Vec::<DiffMessages>::from(
        FlatS3EventMessages::from(transposed_events),
    ));
    let database_records: HashSet<DiffMessages> =
        HashSet::from_iter(Vec::<DiffMessages>::from(database_records));

    // Note, it isn't strictly necessary to perform a diff as the database will handle duplicate
    // records, however this saves some unnecessary database processing.
    let diff = &transposed_events - &database_records;

    if diff.is_empty() {
        debug!("no diff found between database and inventory");
        Ok(database_client)
    } else {
        debug!("diff found between database and inventory: {:#?}", diff);

        // Note, not using collector here because we don't want to call head on all the objects.
        // This means that objects are assumed to exist when ingesting, and it is not confirmed whether
        // this is true. In practice, objects could have been deleted after the inventory was created
        // unless the state of the S3 bucket was kept the same.
        // TODO: add option to check for object existence with HeadObject before ingesting.
        let events = EventSourceType::S3(TransposedS3EventMessages::from(
            FlatS3EventMessages::from(diff.into_iter().collect_vec()),
        ));

        database_client.ingest(events).await?;
        Ok(database_client)
    }
}

/// Create a postgres database pool using an IAM credential generator.
pub async fn create_database_pool(env_config: &EnvConfig) -> Result<DatabaseConnection> {
    let client = Client::from_generator(
        Some(IamGeneratorBuilder::default().build(env_config).await?),
        env_config,
    )
    .await?;

    Ok(client.into_inner())
}

/// Update connection options with new credentials.
/// Todo, replace this with sqlx `before_connect` once it is implemented.
pub async fn update_credentials(
    connection: &DatabaseConnection,
    env_config: &EnvConfig,
) -> Result<()> {
    connection
        .get_postgres_connection_pool()
        .set_connect_options(
            Client::pg_connect_options(
                Some(IamGeneratorBuilder::default().build(env_config).await?),
                env_config,
            )
            .await?,
        );

    Ok(())
}

#[cfg(test)]
pub(crate) mod tests {
    use std::future::Future;

    use aws_lambda_events::sqs::SqsMessage;
    use chrono::DateTime;
    use sqlx::postgres::PgRow;
    use sqlx::PgPool;

    use super::*;
    use crate::database::aws::ingester::tests::{
        assert_row, expected_message, fetch_results, remove_version_ids, test_events, test_ingester,
    };
    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::entities::sea_orm_active_enums::{ArchiveStatus, Reason};
    use crate::events::aws::collecter::tests::{s3_client_expectations, sqs_client_expectations};
    use crate::events::aws::inventory::tests::{
        csv_manifest_from_key_expectations, EXPECTED_LAST_MODIFIED_ONE,
        EXPECTED_LAST_MODIFIED_THREE, EXPECTED_LAST_MODIFIED_TWO, EXPECTED_QUOTED_E_TAG_KEY_2,
        MANIFEST_BUCKET,
    };
    use crate::events::aws::message::default_version_id;
    use crate::events::aws::message::EventType::Deleted;
    use crate::events::aws::tests::{
        expected_event_record_simple, EXPECTED_QUOTED_E_TAG, EXPECTED_SEQUENCER_CREATED_ONE,
        EXPECTED_SEQUENCER_CREATED_TWO, EXPECTED_SEQUENCER_DELETED_ONE, EXPECTED_SHA256,
        EXPECTED_VERSION_ID,
    };
    use crate::events::aws::FlatS3EventMessage;
    use crate::events::EventSourceType::S3;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_receive_and_ingest(pool: PgPool) {
        let client = Client::from_pool(pool);
        test_receive_and_ingest_with(&client, |sqs_client, s3_client| async {
            let config = Default::default();
            receive_and_ingest(s3_client, sqs_client, Some("url"), &client, &config)
                .await
                .unwrap();
        })
        .await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_ingest_event(pool: PgPool) {
        let s3_client = s3_client_expectations();

        let event = SqsEvent {
            records: vec![SqsMessage {
                body: Some(expected_event_record_simple(false)),
                ..Default::default()
            }],
        };

        let ingester = ingest_event(
            event,
            s3_client,
            Client::from_pool(pool),
            &Default::default(),
        )
        .await
        .unwrap();

        let s3_object_results = fetch_results(&ingester).await;

        assert_eq!(s3_object_results.len(), 2);
        let message = expected_message(Some(0), EXPECTED_VERSION_ID.to_string(), false, Created)
            .with_archive_status(Some(ArchiveStatus::DeepArchiveAccess));
        assert_row(
            &s3_object_results[1],
            message,
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            Some(Default::default()),
        );

        let message = expected_message(None, EXPECTED_VERSION_ID.to_string(), false, Deleted)
            .with_sha256(None)
            .with_last_modified_date(None);
        assert_row(
            &s3_object_results[0],
            message,
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            Some(Default::default()),
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_inventory_ingestion(pool: PgPool) {
        assert_ingested_inventory_records(pool).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_inventory_ingestion_existing_records(pool: PgPool) {
        let client = csv_manifest_from_key_expectations();

        let ingester = ingest_s3_inventory(
            client,
            Client::from_pool(pool.clone()),
            Some(MANIFEST_BUCKET.to_string()),
            Some("manifest.json".to_string()),
            None,
            &Default::default(),
        )
        .await
        .unwrap();

        // Delete a record so that the next ingestion has copies from before.
        sqlx::query("delete from s3_object where key = 'inventory_test/key1'")
            .execute(ingester.pool())
            .await
            .unwrap();
        let s3_object_results = s3_object_results(&pool).await;
        assert_eq!(s3_object_results.len(), 2);

        // Records should be the same once ingested again.
        assert_ingested_inventory_records(pool).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_inventory_ingestion_reorder_created(pool: PgPool) {
        let mut events = remove_version_ids(test_events(Some(Created)));
        events
            .reasons
            .iter_mut()
            .for_each(|reason| *reason = Reason::Crawl);

        let (s3_object_results, message) =
            test_inventory_ingestion_reorder(pool, remove_version_ids(events)).await;
        assert_row(
            &s3_object_results[3],
            message.clone().with_is_current_state(false),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            Some(DateTime::default()),
        );
        assert_row(
            &s3_object_results[4],
            message.with_size(None).with_event_type(Deleted),
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            Some(DateTime::default()),
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_inventory_ingestion_reorder_delete_event(pool: PgPool) {
        let mut events = remove_version_ids(test_events(Some(Created)));
        events.sequencers[0] = Some(EXPECTED_SEQUENCER_CREATED_TWO.to_string());
        events
            .reasons
            .iter_mut()
            .for_each(|reason| *reason = Reason::Crawl);

        let (s3_object_results, message) = test_inventory_ingestion_reorder(pool, events).await;
        assert_row(
            &s3_object_results[3],
            message
                .clone()
                .with_size(None)
                .with_event_type(Deleted)
                .with_is_current_state(false),
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            Some(DateTime::default()),
        );
        assert_row(
            &s3_object_results[4],
            message.with_is_current_state(true),
            Some(EXPECTED_SEQUENCER_CREATED_TWO.to_string()),
            Some(DateTime::default()),
        );
    }

    pub(crate) async fn test_receive_and_ingest_with<F, Fut>(client: &Client, f: F)
    where
        F: FnOnce(SQSClient, S3Client) -> Fut,
        Fut: Future<Output = ()>,
    {
        let sqs_client = sqs_client_expectations();
        let s3_client = s3_client_expectations();

        f(sqs_client, s3_client).await;

        let s3_object_results = fetch_results(client).await;

        assert_eq!(s3_object_results.len(), 2);
        let message = expected_message(Some(0), EXPECTED_VERSION_ID.to_string(), false, Created)
            .with_is_current_state(false)
            .with_archive_status(Some(ArchiveStatus::DeepArchiveAccess));
        assert_row(
            &s3_object_results[1],
            message,
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            Some(Default::default()),
        );

        let message = expected_message(None, EXPECTED_VERSION_ID.to_string(), false, Deleted)
            .with_sha256(None)
            .with_last_modified_date(None)
            .with_is_current_state(false);
        assert_row(
            &s3_object_results[0],
            message,
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            Some(Default::default()),
        );
    }

    async fn test_inventory_ingestion_reorder(
        pool: PgPool,
        mut created_events: TransposedS3EventMessages,
    ) -> (Vec<PgRow>, FlatS3EventMessage) {
        let client = csv_manifest_from_key_expectations();

        ingest_s3_inventory(
            client,
            Client::from_pool(pool.clone()),
            Some(MANIFEST_BUCKET.to_string()),
            Some("manifest.json".to_string()),
            None,
            &Default::default(),
        )
        .await
        .unwrap();

        // Ingested a deleted event on the same bucket, key and version_id should automatically binds
        // to the inventory record.
        let mut events = remove_version_ids(test_events(Some(Deleted)));
        events
            .reasons
            .iter_mut()
            .for_each(|reason| *reason = Reason::Crawl);

        events.keys = vec!["inventory_test/key1".to_string()];
        let ingester = test_ingester(pool.clone());
        ingester.ingest(S3(events)).await.unwrap();

        // A new created event that occurs after, on the same key should not interfere with this.
        created_events.keys = vec!["inventory_test/key1".to_string()];
        let ingester = test_ingester(pool.clone());
        ingester.ingest(S3(created_events)).await.unwrap();

        let s3_object_results = s3_object_results(&pool).await;

        assert_eq!(s3_object_results.len(), 5);
        assert_inventory_records(
            &s3_object_results[0],
            "inventory_test/".to_string(),
            0,
            EXPECTED_LAST_MODIFIED_ONE,
            EXPECTED_QUOTED_E_TAG,
            true,
        );
        assert_inventory_records(
            &s3_object_results[1],
            "inventory_test/key1".to_string(),
            0,
            EXPECTED_LAST_MODIFIED_TWO,
            EXPECTED_QUOTED_E_TAG,
            false,
        );
        assert_inventory_records(
            &s3_object_results[2],
            "inventory_test/key2".to_string(),
            5,
            EXPECTED_LAST_MODIFIED_THREE,
            EXPECTED_QUOTED_E_TAG_KEY_2,
            true,
        );

        (
            s3_object_results,
            FlatS3EventMessage::default()
                .with_bucket("bucket".to_string())
                .with_key("inventory_test/key1".to_string())
                .with_size(Some(0))
                .with_version_id(default_version_id())
                .with_e_tag(Some(EXPECTED_QUOTED_E_TAG.to_string()))
                .with_last_modified_date(Some(DateTime::default()))
                .with_sha256(Some(EXPECTED_SHA256.to_string()))
                .with_is_current_state(false)
                .with_reason(Reason::Crawl),
        )
    }

    async fn assert_ingested_inventory_records(pool: PgPool) {
        let client = csv_manifest_from_key_expectations();

        ingest_s3_inventory(
            client,
            Client::from_pool(pool.clone()),
            Some(MANIFEST_BUCKET.to_string()),
            Some("manifest.json".to_string()),
            None,
            &Default::default(),
        )
        .await
        .unwrap();

        let s3_object_results = s3_object_results(&pool).await;

        assert_eq!(s3_object_results.len(), 3);
        assert_inventory_records(
            &s3_object_results[0],
            "inventory_test/".to_string(),
            0,
            EXPECTED_LAST_MODIFIED_ONE,
            EXPECTED_QUOTED_E_TAG,
            true,
        );
        assert_inventory_records(
            &s3_object_results[1],
            "inventory_test/key1".to_string(),
            0,
            EXPECTED_LAST_MODIFIED_TWO,
            EXPECTED_QUOTED_E_TAG,
            true,
        );
        assert_inventory_records(
            &s3_object_results[2],
            "inventory_test/key2".to_string(),
            5,
            EXPECTED_LAST_MODIFIED_THREE,
            EXPECTED_QUOTED_E_TAG_KEY_2,
            true,
        );
    }

    fn assert_inventory_records(
        row: &PgRow,
        key: String,
        size: i64,
        last_modified: &str,
        e_tag: &str,
        is_current_state: bool,
    ) {
        let message = FlatS3EventMessage::default()
            .with_bucket("bucket".to_string())
            .with_key(key)
            .with_size(Some(size))
            .with_version_id(default_version_id())
            .with_last_modified_date(Some(last_modified.parse().unwrap()))
            .with_e_tag(Some(e_tag.to_string()))
            .with_is_current_state(is_current_state)
            .with_reason(Reason::Crawl);

        assert_row(
            row,
            message,
            Some("000000000000000000000000000000-0100000000000000".to_string()),
            None,
        );
    }

    pub(crate) async fn s3_object_results(pool: &PgPool) -> Vec<PgRow> {
        sqlx::query("select * from s3_object order by sequencer, key")
            .fetch_all(pool)
            .await
            .unwrap()
    }
}
