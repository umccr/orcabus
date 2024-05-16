//! Event handlers for AWS, such as Lambda event handlers.
//!

use aws_lambda_events::sqs::SqsEvent;
use itertools::Itertools;
use lambda_runtime::Error;
use mockall_double::double;
use sqlx::PgPool;
use std::collections::HashSet;
use tracing::{debug, trace};

#[double]
use crate::clients::aws::s3::Client as S3Client;
#[double]
use crate::clients::aws::sqs::Client as SQSClient;
use crate::database::aws::credentials::IamGeneratorBuilder;
use crate::database::aws::ingester::Ingester;
use crate::database::aws::query::Query;
use crate::database::{Client, Ingest};
use crate::events::aws::collecter::CollecterBuilder;
use crate::events::aws::inventory::{DiffMessages, Inventory, Manifest};
use crate::events::aws::{Events, FlatS3EventMessages, TransposedS3EventMessages};
use crate::events::{Collect, EventSourceType};

/// Handle SQS events by manually calling the SQS receive function. This is meant
/// to be run through something like API gateway to manually invoke ingestion.
pub async fn receive_and_ingest(
    s3_client: S3Client,
    sqs_client: SQSClient,
    sqs_url: Option<impl Into<String>>,
    database_client: Client<'_>,
) -> Result<Ingester<'_>, Error> {
    let events = CollecterBuilder::default()
        .with_s3_client(s3_client)
        .with_sqs_client(sqs_client)
        .set_sqs_url(sqs_url)
        .build_receive()
        .await?
        .collect()
        .await?;

    let ingester = Ingester::new(database_client);

    ingester.ingest(events).await?;

    Ok(ingester)
}

/// Handle SQS events that go through an SqsEvent.
pub async fn ingest_event(
    event: SqsEvent,
    s3_client: S3Client,
    database_client: Client<'_>,
) -> Result<Ingester<'_>, Error> {
    trace!("received event: {:?}", event);

    let events: FlatS3EventMessages = event
        .records
        .into_iter()
        .filter_map(|event| {
            event.body.map(|body| {
                let body: Option<FlatS3EventMessages> = serde_json::from_str(&body)?;
                Ok(body.unwrap_or_default())
            })
        })
        .collect::<Result<Vec<FlatS3EventMessages>, Error>>()?
        .into();

    trace!("flattened events: {:?}", events);

    let events = CollecterBuilder::default()
        .with_s3_client(s3_client)
        .build(events)
        .await
        .collect()
        .await?;

    trace!("ingesting events: {:?}", events);

    let ingester = Ingester::new(database_client);

    trace!("ingester: {:?}", ingester);
    ingester.ingest(events).await?;

    Ok(ingester)
}

/// Handle an S3 inventory for ingestion.
pub async fn ingest_s3_inventory(
    s3_client: S3Client,
    database_client: Client<'_>,
    bucket: Option<String>,
    key: Option<String>,
    manifest: Option<Manifest>,
) -> Result<Ingester<'_>, Error> {
    let inventory = Inventory::new(s3_client);

    let records = if let Some(manifest) = manifest {
        inventory.parse_manifest(manifest).await?
    } else if let (Some(bucket), Some(key)) = (bucket, key) {
        inventory.parse_manifest_key(key, bucket).await?
    } else {
        return Err(Error::from(
            "either a manifest or bucket and key option needs to be specified".to_string(),
        ));
    };
    trace!("records extracted from inventory: {:?}", records);

    let transposed_events: TransposedS3EventMessages =
        FlatS3EventMessages::from(records).sort_and_dedup().into();

    let query = Query::new(database_client.clone());
    let mut tx = query.transaction().await?;
    let database_records = query
        .select_existing_by_bucket_key(
            &mut tx,
            transposed_events.keys.as_slice(),
            transposed_events.buckets.as_slice(),
            transposed_events.version_ids.as_slice(),
        )
        .await?;
    tx.commit().await?;

    // Some back and forth between transposed vs not transposed events. Potential optimization
    // could involve using ndarray + slicing, with an enum representing the fields of the struct.
    let transposed_events: HashSet<DiffMessages> = HashSet::from_iter(Vec::<DiffMessages>::from(
        FlatS3EventMessages::from(transposed_events),
    ));
    let database_records: HashSet<DiffMessages> =
        HashSet::from_iter(Vec::<DiffMessages>::from(database_records));
    let diff = &transposed_events - &database_records;

    if diff.is_empty() {
        debug!("no diff found between database and inventory");
        Ok(Ingester::new(database_client))
    } else {
        debug!("diff found between database and inventory: {:?}", diff);

        // Note, not using collector here because we don't want to call head on all the objects.
        // This means that objects are assumed to exist when ingesting, and it is not confirmed whether
        // this is true. In practice, objects could have been deleted after the inventory was created
        // unless the state of the S3 bucket was kept the same.
        // TODO: add option to check for object existence with HeadObject before ingesting.
        let events = EventSourceType::S3(Events::from(FlatS3EventMessages::from(
            diff.into_iter().collect_vec(),
        )));

        let ingester = Ingester::new(database_client);
        trace!("ingester: {:?}", ingester);

        ingester.ingest(events).await?;

        Ok(ingester)
    }
}

/// Create a postgres database pool using an IAM credential generator.
pub async fn create_database_pool() -> Result<PgPool, Error> {
    Ok(Client::create_pool(Some(IamGeneratorBuilder::default().build().await?)).await?)
}

/// Update connection options with new credentials.
/// Todo, replace this with sqlx `before_connect` once it is implemented.
pub async fn update_credentials(pool: &PgPool) -> Result<(), Error> {
    pool.set_connect_options(
        Client::connect_options(Some(IamGeneratorBuilder::default().build().await?)).await?,
    );

    Ok(())
}

#[cfg(test)]
mod tests {
    use aws_lambda_events::sqs::SqsMessage;
    use chrono::DateTime;
    use sqlx::postgres::PgRow;

    use crate::database::aws::ingester::tests::{
        assert_ingest_events, assert_row, fetch_results, remove_version_ids, replace_sequencers,
        test_created_events, test_events, test_ingester,
    };
    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::events::aws::collecter::tests::{
        expected_head_object, set_s3_client_expectations, set_sqs_client_expectations,
    };
    use crate::events::aws::inventory::tests::{
        csv_manifest_from_key_expectations, EXPECTED_E_TAG_EMPTY, EXPECTED_E_TAG_KEY_2,
        EXPECTED_LAST_MODIFIED_ONE, EXPECTED_LAST_MODIFIED_THREE, EXPECTED_LAST_MODIFIED_TWO,
        MANIFEST_BUCKET,
    };
    use crate::events::aws::tests::{
        expected_event_record_simple, EXPECTED_SEQUENCER_CREATED_ONE,
        EXPECTED_SEQUENCER_CREATED_TWO, EXPECTED_SEQUENCER_DELETED_ONE, EXPECTED_SHA256,
        EXPECTED_VERSION_ID,
    };
    use crate::events::aws::FlatS3EventMessage;

    use super::*;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_receive_and_ingest(pool: PgPool) {
        let mut sqs_client = SQSClient::default();
        let mut s3_client = S3Client::default();

        set_sqs_client_expectations(&mut sqs_client);
        set_s3_client_expectations(&mut s3_client, vec![|| Ok(expected_head_object())]);

        let ingester = receive_and_ingest(s3_client, sqs_client, Some("url"), Client::new(pool))
            .await
            .unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 1);
        assert_eq!(s3_object_results.len(), 1);
        assert_ingest_events(&s3_object_results[0], EXPECTED_VERSION_ID);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_ingest_event(pool: PgPool) {
        let mut s3_client = S3Client::default();

        set_s3_client_expectations(&mut s3_client, vec![|| Ok(expected_head_object())]);

        let event = SqsEvent {
            records: vec![SqsMessage {
                body: Some(expected_event_record_simple()),
                ..Default::default()
            }],
        };

        let ingester = ingest_event(event, s3_client, Client::new(pool))
            .await
            .unwrap();

        let (object_results, s3_object_results) = fetch_results(&ingester).await;

        assert_eq!(object_results.len(), 1);
        assert_eq!(s3_object_results.len(), 1);
        assert_ingest_events(&s3_object_results[0], EXPECTED_VERSION_ID);
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
            Client::new(pool.clone()),
            Some(MANIFEST_BUCKET.to_string()),
            Some("manifest.json".to_string()),
            None,
        )
        .await
        .unwrap();

        // Delete a record so that the next ingestion has copies from before.
        sqlx::query!("delete from s3_object where key = 'inventory_test/key1'")
            .execute(ingester.client().pool())
            .await
            .unwrap();
        let s3_object_results = s3_object_results(&pool).await;
        assert_eq!(s3_object_results.len(), 2);

        // Records should be the same once ingested again.
        assert_ingested_inventory_records(pool).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_inventory_ingestion_binding_old_created(pool: PgPool) {
        let client = csv_manifest_from_key_expectations();

        ingest_s3_inventory(
            client,
            Client::new(pool.clone()),
            Some(MANIFEST_BUCKET.to_string()),
            Some("manifest.json".to_string()),
            None,
        )
        .await
        .unwrap();

        // Ingested a deleted event on the same bucket, key and version_id should automatically binds
        // to the inventory record.
        let mut events = remove_version_ids(test_events());
        events.object_created = Default::default();
        events.object_deleted.keys = vec!["inventory_test/key1".to_string()];
        let ingester = test_ingester(pool.clone());
        ingester.ingest_events(events).await.unwrap();

        // A new created event that occurs before on the same key, should trigger a reorder.
        let mut events = remove_version_ids(test_created_events());
        events.object_created.keys = vec!["inventory_test/key1".to_string()];
        let ingester = test_ingester(pool.clone());
        ingester.ingest_events(events).await.unwrap();

        let s3_object_results = s3_object_results(&pool).await;

        assert_eq!(s3_object_results.len(), 3);
        assert_inventory_records(
            &s3_object_results[0],
            "inventory_test/".to_string(),
            0,
            EXPECTED_LAST_MODIFIED_ONE,
            EXPECTED_E_TAG_EMPTY,
        );

        let message = FlatS3EventMessage::default()
            .with_bucket("bucket".to_string())
            .with_key("inventory_test/key1".to_string())
            .with_size(Some(0))
            .with_version_id(FlatS3EventMessage::default_version_id().to_string())
            .with_e_tag(Some(EXPECTED_E_TAG_EMPTY.to_string()))
            .with_last_modified_date(Some(DateTime::default()))
            .with_sha256(Some(EXPECTED_SHA256.to_string()));
        assert_row(
            &s3_object_results[1],
            message.clone(),
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            Some(DateTime::default()),
            Some(DateTime::default()),
        );

        assert_inventory_records(
            &s3_object_results[2],
            "inventory_test/key2".to_string(),
            5,
            EXPECTED_LAST_MODIFIED_THREE,
            EXPECTED_E_TAG_KEY_2,
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_inventory_ingestion_binding_delete_event(pool: PgPool) {
        let client = csv_manifest_from_key_expectations();

        ingest_s3_inventory(
            client,
            Client::new(pool.clone()),
            Some(MANIFEST_BUCKET.to_string()),
            Some("manifest.json".to_string()),
            None,
        )
        .await
        .unwrap();

        // Ingested a deleted event on the same bucket, key and version_id should automatically binds
        // to the inventory record.
        let mut events = remove_version_ids(test_events());
        events.object_created = Default::default();
        events.object_deleted.keys = vec!["inventory_test/key1".to_string()];
        let ingester = test_ingester(pool.clone());
        ingester.ingest_events(events).await.unwrap();

        // A new created event that occurs after, on the same key should not interfere with this.
        let mut events = replace_sequencers(
            remove_version_ids(test_created_events()),
            Some(EXPECTED_SEQUENCER_CREATED_TWO.to_string()),
        );
        events.object_created.keys = vec!["inventory_test/key1".to_string()];
        let ingester = test_ingester(pool.clone());
        ingester.ingest_events(events).await.unwrap();

        let s3_object_results = s3_object_results(&pool).await;

        assert_eq!(s3_object_results.len(), 4);
        assert_inventory_records(
            &s3_object_results[0],
            "inventory_test/".to_string(),
            0,
            EXPECTED_LAST_MODIFIED_ONE,
            EXPECTED_E_TAG_EMPTY,
        );

        let message = FlatS3EventMessage::default()
            .with_bucket("bucket".to_string())
            .with_key("inventory_test/key1".to_string())
            .with_size(Some(0))
            .with_version_id(FlatS3EventMessage::default_version_id().to_string())
            .with_last_modified_date(Some(EXPECTED_LAST_MODIFIED_TWO.parse().unwrap()))
            .with_e_tag(Some(EXPECTED_E_TAG_EMPTY.to_string()));
        assert_row(
            &s3_object_results[1],
            message.clone(),
            Some("".to_string()),
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            None,
            Some(DateTime::default()),
        );

        let message = message
            .with_last_modified_date(Some(DateTime::default()))
            .with_sha256(Some(EXPECTED_SHA256.to_string()));
        assert_row(
            &s3_object_results[2],
            message,
            Some(EXPECTED_SEQUENCER_CREATED_TWO.to_string()),
            None,
            Some(DateTime::default()),
            None,
        );

        assert_inventory_records(
            &s3_object_results[3],
            "inventory_test/key2".to_string(),
            5,
            EXPECTED_LAST_MODIFIED_THREE,
            EXPECTED_E_TAG_KEY_2,
        );
    }

    async fn assert_ingested_inventory_records(pool: PgPool) {
        let client = csv_manifest_from_key_expectations();

        ingest_s3_inventory(
            client,
            Client::new(pool.clone()),
            Some(MANIFEST_BUCKET.to_string()),
            Some("manifest.json".to_string()),
            None,
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
            EXPECTED_E_TAG_EMPTY,
        );
        assert_inventory_records(
            &s3_object_results[1],
            "inventory_test/key1".to_string(),
            0,
            EXPECTED_LAST_MODIFIED_TWO,
            EXPECTED_E_TAG_EMPTY,
        );
        assert_inventory_records(
            &s3_object_results[2],
            "inventory_test/key2".to_string(),
            5,
            EXPECTED_LAST_MODIFIED_THREE,
            EXPECTED_E_TAG_KEY_2,
        );
    }

    fn assert_inventory_records(
        row: &PgRow,
        key: String,
        size: i64,
        last_modified: &str,
        e_tag: &str,
    ) {
        let message = FlatS3EventMessage::default()
            .with_bucket("bucket".to_string())
            .with_key(key)
            .with_size(Some(size))
            .with_version_id(FlatS3EventMessage::default_version_id().to_string())
            .with_last_modified_date(Some(last_modified.parse().unwrap()))
            .with_e_tag(Some(e_tag.to_string()));

        assert_row(row, message, Some("".to_string()), None, None, None);
    }

    async fn s3_object_results(pool: &PgPool) -> Vec<PgRow> {
        sqlx::query("select * from s3_object order by key")
            .fetch_all(pool)
            .await
            .unwrap()
    }
}
