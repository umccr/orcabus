//! Definition and implementation of the aws Collecter.
//!

use crate::clients::aws::s3::Client as S3Client;
use crate::clients::aws::sqs::Client as SQSClient;
use crate::database;
use crate::database::entities::s3_object;
use crate::database::entities::sea_orm_active_enums::ArchiveStatus;
use crate::env::Config;
use crate::error::Error::{S3Error, SQSError, SerdeError};
use crate::error::{Error, Result};
use crate::events::aws::{
    EventType, FlatS3EventMessage, FlatS3EventMessages, StorageClass, TransposedS3EventMessages,
};
use crate::events::{Collect, EventSource, EventSourceType};
use crate::queries::list::ListQueryBuilder;
use crate::routes::filter::S3ObjectsFilter;
use crate::uuid::UuidGenerator;
use async_trait::async_trait;
use aws_sdk_s3::error::BuildError;
use aws_sdk_s3::operation::get_object_tagging::GetObjectTaggingOutput;
use aws_sdk_s3::operation::head_object::HeadObjectOutput;
use aws_sdk_s3::primitives;
use aws_sdk_s3::types::StorageClass::Standard;
use aws_sdk_s3::types::{Tag, Tagging};
use chrono::{DateTime, Utc};
use futures::future::join_all;
use futures::TryFutureExt;
use std::str::FromStr;
use tracing::{trace, warn};
use uuid::Uuid;

/// Build an AWS collector struct.
#[derive(Default, Debug)]
pub struct CollecterBuilder {
    s3_client: Option<S3Client>,
    sqs_client: Option<SQSClient>,
    sqs_url: Option<String>,
}

impl CollecterBuilder {
    /// Build with the S3 client.
    pub fn with_s3_client(mut self, client: S3Client) -> Self {
        self.s3_client = Some(client);
        self
    }

    /// Build with the SQS client.
    pub fn with_sqs_client(mut self, client: SQSClient) -> Self {
        self.sqs_client = Some(client);
        self
    }

    /// Build with the SQS url.
    pub fn with_sqs_url(self, url: impl Into<String>) -> Self {
        self.set_sqs_url(Some(url))
    }

    /// Set the SQS url to build with.
    pub fn set_sqs_url(mut self, url: Option<impl Into<String>>) -> Self {
        self.sqs_url = url.map(|url| url.into());
        self
    }

    /// Build a collector using the raw events.
    pub async fn build<'a>(
        self,
        raw_events: FlatS3EventMessages,
        config: &'a Config,
        client: &'a database::Client,
    ) -> Collecter<'a> {
        if let Some(s3_client) = self.s3_client {
            Collecter::new(s3_client, client, raw_events, config)
        } else {
            Collecter::new(S3Client::with_defaults().await, client, raw_events, config)
        }
    }

    /// Manually call the receive function to retrieve events from the SQS queue.
    pub async fn receive(client: &SQSClient, url: &str) -> Result<FlatS3EventMessages> {
        let message_output = client
            .receive_message(url)
            .await
            .map_err(|err| SQSError(err.into_service_error().to_string()))?;

        let event_messages: FlatS3EventMessages = message_output
            .messages
            .unwrap_or_default()
            .into_iter()
            .map(|message| {
                trace!(message = ?message, "got the message");

                if let Some(body) = message.body() {
                    let events: Option<FlatS3EventMessages> =
                        serde_json::from_str(body).map_err(|err| SerdeError(err.to_string()))?;
                    Ok(events.unwrap_or_default())
                } else {
                    Err(SQSError("No body in SQS message".to_string()))
                }
            })
            .collect::<Result<Vec<FlatS3EventMessages>>>()?
            .into();

        Ok(event_messages)
    }

    /// Build a collector by manually calling receive to obtain the raw events.
    pub async fn build_receive<'a>(
        mut self,
        config: &'a Config,
        database_client: &'a database::Client,
    ) -> Result<Collecter<'a>> {
        let url = self.sqs_url.take();
        let url = Config::value_or_else(url.as_deref(), config.sqs_url())?;

        let client = self.sqs_client.take();
        if let Some(sqs_client) = &client {
            Ok(self
                .build(
                    Self::receive(sqs_client, url).await?,
                    config,
                    database_client,
                )
                .await)
        } else {
            Ok(self
                .build(
                    Self::receive(&SQSClient::with_defaults().await, url).await?,
                    config,
                    database_client,
                )
                .await)
        }
    }
}

/// Collect raw events into the processed form which the database module accepts. Tracks the
/// number of (potentially duplicate) records that are processed by this collector. The number of
/// records is None before any events have been processed.
#[derive(Debug)]
pub struct Collecter<'a> {
    client: S3Client,
    database_client: &'a database::Client,
    raw_events: FlatS3EventMessages,
    config: &'a Config,
    n_records: Option<usize>,
}

impl<'a> Collecter<'a> {
    /// Create a new collector.
    pub(crate) fn new(
        client: S3Client,
        database_client: &'a database::Client,
        raw_events: FlatS3EventMessages,
        config: &'a Config,
    ) -> Self {
        Self {
            client,
            database_client,
            raw_events,
            config,
            n_records: None,
        }
    }

    /// Get the inner values.
    pub fn into_inner(
        self,
    ) -> (
        S3Client,
        &'a database::Client,
        FlatS3EventMessages,
        &'a Config,
    ) {
        (
            self.client,
            self.database_client,
            self.raw_events,
            self.config,
        )
    }

    /// Converts an AWS datetime to a standard database format.
    pub fn convert_datetime(datetime: Option<primitives::DateTime>) -> Option<DateTime<Utc>> {
        if let Some(head) = datetime {
            DateTime::from_timestamp(head.secs(), head.subsec_nanos())
        } else {
            None
        }
    }

    /// Gets S3 metadata from HeadObject such as creation/archival timestamps and statuses.
    pub async fn head(client: &S3Client, event: FlatS3EventMessage) -> Result<FlatS3EventMessage> {
        let head = client
            .head_object(&event.key, &event.bucket, &event.version_id)
            .inspect_err(|err| {
                warn!("Error received from HeadObject: {}", err);
            })
            .await
            .ok();

        // Race condition: it's possible that an object gets deleted so quickly that it
        // occurs before calling head/tagging. This means that there may be cases where the
        // storage class and other fields are not known, or object moves cannot be tracked.
        let Some(head) = head else {
            return Ok(event);
        };

        trace!(head = ?head, "received HeadObject output");

        let HeadObjectOutput {
            storage_class,
            last_modified,
            content_length,
            e_tag,
            checksum_sha256,
            delete_marker,
            archive_status,
            ..
        } = head;

        // S3 does not return a storage class for standard, which means this is the
        // default. See https://docs.aws.amazon.com/AmazonS3/latest/API/API_HeadObject.html#API_HeadObject_ResponseSyntax
        Ok(event
            .update_storage_class(StorageClass::from_aws(storage_class.unwrap_or(Standard)))
            .update_last_modified_date(Self::convert_datetime(last_modified))
            .update_size(content_length)
            .update_e_tag(e_tag)
            .update_sha256(checksum_sha256)
            .update_delete_marker(delete_marker)
            .update_archive_status(archive_status.and_then(ArchiveStatus::from_aws)))
    }

    /// Gets S3 tags from objects.
    pub async fn tagging(
        config: &Config,
        client: &S3Client,
        database_client: &database::Client,
        event: FlatS3EventMessage,
    ) -> Result<FlatS3EventMessage> {
        let tagging = client
            .get_object_tagging(&event.key, &event.bucket, &event.version_id)
            .inspect_err(|err| {
                warn!("Error received from GetObjectTagging: {}", err);
            })
            .await
            .ok();

        let Some(tagging) = tagging else {
            return Ok(event);
        };

        trace!(tagging = ?tagging, "received tagging output");

        let GetObjectTaggingOutput { mut tag_set, .. } = tagging;

        // Check if the object contains the ingest_id tag.
        let tag = tag_set
            .clone()
            .into_iter()
            .find(|tag| tag.key == config.ingester_tag_name());

        let Some(tag) = tag else {
            // If it doesn't, then a new tag needs to be generated.
            let ingest_id = UuidGenerator::generate();
            let tag = Tag::builder()
                .key(config.ingester_tag_name())
                .value(ingest_id)
                .build()?;
            tag_set.push(tag);

            // Try to push the tags to S3, only proceed if successful.
            let result = client
                .put_object_tagging(
                    &event.key,
                    &event.bucket,
                    &event.version_id,
                    Tagging::builder().set_tag_set(Some(tag_set)).build()?,
                )
                .await
                .inspect_err(|err| {
                    warn!("Error received from PutObjectTagging: {}", err);
                });

            // Only add a ingest_id to the new record if the tagging was successful.
            return if result.is_ok() {
                Ok(event.with_ingest_id(Some(ingest_id)))
            } else {
                Ok(event)
            };
        };

        // The object has a ingest_id tag. Grab the existing the tag, returning a new record without
        // the ingest_id if the is not valid.
        let ingest_id = Uuid::from_str(tag.value()).inspect_err(|err| {
            warn!("Failed to parse ingest_id from tag: {}", err);
        });
        let Ok(ingest_id) = ingest_id else {
            return Ok(event);
        };

        // From here, the new record must be a valid, moved object.
        let event = event.with_ingest_id(Some(ingest_id));

        // Get the attributes from the old record to update the new record with.
        let filter = S3ObjectsFilter {
            ingest_id: vec![ingest_id].into(),
            ..Default::default()
        };
        let moved_object =
            ListQueryBuilder::<_, s3_object::Entity>::new(database_client.connection_ref())
                .filter_all(filter, true, false)?
                .one()
                .await
                .ok()
                .flatten();

        // Update the new record with the attributes if possible, or return the new record without
        // the attributes if not possible.
        if let Some(moved_object) = moved_object {
            Ok(event.with_attributes(moved_object.attributes))
        } else {
            warn!("Object with ingest_id {} not found in database", ingest_id);
            Ok(event)
        }
    }

    /// Process events and add header and datetime fields.
    pub async fn update_events(
        config: &Config,
        client: &S3Client,
        database_client: &database::Client,
        events: FlatS3EventMessages,
    ) -> Result<FlatS3EventMessages> {
        Ok(FlatS3EventMessages(
            join_all(events.into_inner().into_iter().map(|event| async move {
                // No need to run this unnecessarily on removed events.
                match event.event_type {
                    EventType::Deleted | EventType::Other => return Ok(event),
                    _ => {}
                };

                trace!(key = ?event.key, bucket = ?event.bucket, "updating event");

                let event = Self::head(client, event).await?;
                Self::tagging(config, client, database_client, event).await
            }))
            .await
            .into_iter()
            .collect::<Result<Vec<FlatS3EventMessage>>>()?,
        ))
    }

    /// Get the number of records processed.
    pub fn n_records(&self) -> Option<usize> {
        self.n_records
    }
}

impl From<BuildError> for Error {
    fn from(err: BuildError) -> Self {
        S3Error(err.to_string())
    }
}

#[async_trait]
impl Collect for Collecter<'_> {
    async fn collect(mut self) -> Result<EventSource> {
        let (client, database_client, events, config) = self.into_inner();

        let events = events.sort_and_dedup();

        let events = Self::update_events(config, &client, database_client, events).await?;
        // Get only the known event types.
        let events = events.filter_known();
        let n_records = events.0.len();

        if config.paired_ingest_mode() {
            Ok(EventSource::new(
                EventSourceType::S3Paired(events.into()),
                n_records,
            ))
        } else {
            Ok(EventSource::new(
                EventSourceType::S3(TransposedS3EventMessages::from(events)),
                n_records,
            ))
        }
    }
}

#[cfg(test)]
pub(crate) mod tests {
    use aws_smithy_mocks_experimental::mock;
    use aws_smithy_mocks_experimental::Rule;
    use aws_smithy_mocks_experimental::RuleMode;

    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::events::aws::tests::{
        expected_event_record_simple, expected_flat_events_simple, EXPECTED_SHA256,
        EXPECTED_VERSION_ID,
    };
    use crate::events::aws::StorageClass::IntelligentTiering;

    use aws_sdk_s3::operation::get_object_tagging::GetObjectTaggingError;
    use aws_sdk_s3::operation::head_object::HeadObjectError;
    use aws_sdk_s3::operation::put_object_tagging::PutObjectTaggingOutput;

    use aws_sdk_s3::primitives::DateTimeFormat;
    use aws_sdk_s3::types;
    use aws_sdk_s3::types::error::NotFound;
    use aws_sdk_sqs::operation::receive_message::ReceiveMessageOutput;
    use aws_sdk_sqs::types::builders::MessageBuilder;
    use aws_smithy_mocks_experimental::mock_client;
    use sea_orm::prelude::Json;
    use serde_json::json;
    use sqlx::{PgPool, Row};

    use super::*;
    use crate::database::{Client, Ingest};
    use crate::events::aws::message::default_version_id;
    use crate::events::aws::message::EventType::Created;
    use crate::handlers::aws::tests::s3_object_results;
    use crate::queries::EntriesBuilder;

    #[tokio::test]
    async fn receive() {
        let sqs_client = sqs_client_expectations();

        let events = CollecterBuilder::receive(&sqs_client, "url").await.unwrap();

        let mut expected = expected_flat_events_simple();
        expected
            .0
            .iter_mut()
            .zip(&events.0)
            .for_each(|(expected_event, event)| {
                // The object id will be different for each event.
                expected_event.s3_object_id = event.s3_object_id;
            });

        assert_eq!(events, expected);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn build_receive(pool: PgPool) {
        let sqs_client = sqs_client_expectations();
        let s3_client = s3_client_expectations();

        let events = CollecterBuilder::default()
            .with_sqs_client(sqs_client)
            .with_s3_client(s3_client)
            .with_sqs_url("url")
            .build_receive(&Default::default(), &Client::from_pool(pool))
            .await
            .unwrap()
            .collect()
            .await
            .unwrap()
            .into_inner()
            .0;

        assert_collected_events(events);
    }

    #[test]
    fn convert_datetime() {
        let result = Collecter::convert_datetime(Some(
            primitives::DateTime::from_str("1970-01-01T00:00:00Z", DateTimeFormat::DateTime)
                .unwrap(),
        ));

        assert_eq!(result, Some(DateTime::<Utc>::default()));
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn head(pool: PgPool) {
        let config = Default::default();
        let client = Client::from_pool(pool);
        let mut collecter = test_collecter(&config, &client).await;

        collecter.client = mock_s3(&[head_expectation(
            default_version_id(),
            expected_head_object(),
        )]);

        let result = Collecter::head(
            &collecter.client,
            expected_s3_event_message().with_version_id(default_version_id()),
        )
        .await
        .unwrap();
        let expected = result
            .clone()
            .with_sha256(Some(EXPECTED_SHA256.to_string()))
            .with_storage_class(Some(IntelligentTiering))
            .with_last_modified_date(Some(Default::default()));

        assert_eq!(result, expected);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn head_not_found(pool: PgPool) {
        let config = Default::default();
        let client = Client::from_pool(pool);
        let mut collecter = test_collecter(&config, &client).await;

        collecter.client = mock_s3(&[mock!(aws_sdk_s3::Client::head_object)
            .match_requests(move |req| {
                req.key() == Some("key")
                    && req.bucket() == Some("bucket")
                    && req.version_id().is_none()
            })
            .then_error(expected_head_object_not_found)]);

        let result = Collecter::head(
            &collecter.client,
            expected_s3_event_message().with_version_id(default_version_id()),
        )
        .await;
        assert!(result.is_ok());
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_events(pool: PgPool) {
        let config = Default::default();
        let client = Client::from_pool(pool);
        let mut collecter = test_collecter(&config, &client).await;

        let events = expected_flat_events_simple().sort_and_dedup();

        collecter.client = s3_client_expectations();

        let mut result = Collecter::update_events(&config, &collecter.client, &client, events)
            .await
            .unwrap()
            .into_inner()
            .into_iter();

        let first = result.next().unwrap();
        assert_eq!(first.storage_class, Some(IntelligentTiering));
        assert_eq!(first.last_modified_date, Some(Default::default()));

        let second = result.next().unwrap();
        assert_eq!(second.storage_class, None);
        assert_eq!(second.last_modified_date, None);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn tagging_without_move(pool: PgPool) {
        let config = Default::default();
        let client = Client::from_pool(pool.clone());
        let mut collecter = test_collecter(&config, &client).await;

        collecter.raw_events = FlatS3EventMessages(vec![
            expected_s3_event_message().with_version_id(EXPECTED_VERSION_ID.to_string())
        ]);
        collecter.client = s3_client_expectations();

        let mut result = collecter.collect().await.unwrap();
        let EventSourceType::S3(events) = &mut result.event_type else {
            panic!();
        };
        assert!(events.ingest_ids[0].is_some());

        client.ingest(result.event_type).await.unwrap();

        let s3_object_results = s3_object_results(&pool).await;
        assert_eq!(s3_object_results.len(), 1);
        assert!(s3_object_results[0]
            .get::<Option<Uuid>, _>("ingest_id")
            .is_some());
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn tagging_with_move(pool: PgPool) {
        let config = Default::default();
        let client = Client::from_pool(pool.clone());
        let mut collecter = test_collecter(&config, &client).await;

        let ingest_id = UuidGenerator::generate();
        EntriesBuilder::default()
            .with_ingest_id(ingest_id)
            .with_n(1)
            .build(&client)
            .await
            .unwrap();

        collecter.raw_events = FlatS3EventMessages(vec![
            expected_s3_event_message().with_version_id(default_version_id())
        ]);
        collecter.client = mock_s3(&[
            head_expectation(default_version_id(), expected_head_object()),
            get_tagging_expectation(
                default_version_id(),
                GetObjectTaggingOutput::builder()
                    .set_tag_set(Some(vec![Tag::builder()
                        .key("ingest_id")
                        .value(ingest_id.to_string())
                        .build()
                        .unwrap()]))
                    .build()
                    .unwrap(),
            ),
        ]);

        let mut result = collecter.collect().await.unwrap();
        let EventSourceType::S3(events) = &mut result.event_type else {
            panic!();
        };
        assert!(events.ingest_ids[0].is_some());

        client.ingest(result.event_type).await.unwrap();

        let s3_object_results = s3_object_results(&pool).await;
        assert_eq!(s3_object_results.len(), 2);
        assert_eq!(
            s3_object_results[0].get::<Option<Uuid>, _>("ingest_id"),
            Some(ingest_id)
        );
        assert_eq!(
            s3_object_results[1].get::<Option<Uuid>, _>("ingest_id"),
            Some(ingest_id)
        );

        let expected_attributes = json!({
            "attributeId": "0",
            "nestedId": {
                "attributeId": "0"
            }
        });
        assert_eq!(
            s3_object_results[0].get::<Option<Json>, _>("attributes"),
            Some(expected_attributes.clone())
        );
        assert_eq!(
            s3_object_results[1].get::<Option<Json>, _>("attributes"),
            Some(expected_attributes)
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn tagging_on_fail(pool: PgPool) {
        let config = Default::default();
        let client = Client::from_pool(pool.clone());
        let mut collecter = test_collecter(&config, &client).await;

        collecter.raw_events = FlatS3EventMessages(vec![
            expected_s3_event_message().with_version_id(default_version_id())
        ]);

        collecter.client = mock_s3(&[
            head_expectation(default_version_id(), expected_head_object()),
            mock!(aws_sdk_s3::Client::get_object_tagging)
                .match_requests(move |req| {
                    req.key() == Some("key")
                        && req.bucket() == Some("bucket")
                        && req.version_id().is_none()
                })
                .then_error(move || GetObjectTaggingError::unhandled("unhandled")),
        ]);

        let mut result = collecter.collect().await.unwrap();
        let EventSourceType::S3(events) = &mut result.event_type else {
            panic!();
        };
        assert!(events.ingest_ids[0].is_none());

        client.ingest(result.event_type).await.unwrap();

        let s3_object_results = s3_object_results(&pool).await;
        assert_eq!(s3_object_results.len(), 1);
        assert!(s3_object_results[0]
            .get::<Option<Uuid>, _>("ingest_id")
            .is_none());
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn collect(pool: PgPool) {
        let config = Default::default();
        let client = Client::from_pool(pool);
        let mut collecter = test_collecter(&config, &client).await;
        collecter.client = s3_client_expectations();

        let result = collecter.collect().await.unwrap().into_inner().0;

        assert_collected_events(result);
    }

    fn expected_s3_event_message() -> FlatS3EventMessage {
        FlatS3EventMessage::new_with_generated_id()
            .with_event_type(Created)
            .with_key("key".to_string())
            .with_bucket("bucket".to_string())
    }

    pub(crate) fn assert_collected_events(result: EventSourceType) {
        match result {
            EventSourceType::S3(events) => {
                assert_eq!(events.storage_classes[0], Some(IntelligentTiering));
                assert_eq!(events.last_modified_dates[0], Some(Default::default()));

                assert_eq!(events.storage_classes[1], None);
                assert_eq!(events.last_modified_dates[1], None);
            }
            _ => panic!("unexpected event type"),
        }
    }

    pub(crate) fn head_expectation(version_id: String, output: HeadObjectOutput) -> Rule {
        mock!(aws_sdk_s3::Client::head_object)
            .match_requests(move |req| {
                req.key() == Some("key")
                    && req.bucket() == Some("bucket")
                    && ((version_id != default_version_id()
                        && req.version_id() == Some(&version_id.to_string()))
                        || (version_id == default_version_id() && req.version_id().is_none()))
            })
            .then_output(move || output.clone())
    }

    pub(crate) fn put_tagging_expectation(
        version_id: String,
        output: PutObjectTaggingOutput,
    ) -> Rule {
        mock!(aws_sdk_s3::Client::put_object_tagging)
            .match_requests(move |req| {
                req.key() == Some("key")
                    && req.bucket() == Some("bucket")
                    && ((version_id != default_version_id()
                        && req.version_id() == Some(&version_id.to_string()))
                        || (version_id == default_version_id() && req.version_id().is_none()))
                    && req
                        .tagging()
                        .is_some_and(|t| t.tag_set().first().unwrap().key() == "ingest_id")
            })
            .then_output(move || output.clone())
    }

    pub(crate) fn get_tagging_expectation(
        version_id: String,
        output: GetObjectTaggingOutput,
    ) -> Rule {
        mock!(aws_sdk_s3::Client::get_object_tagging)
            .match_requests(move |req| {
                req.key() == Some("key")
                    && req.bucket() == Some("bucket")
                    && ((version_id != default_version_id()
                        && req.version_id() == Some(&version_id.to_string()))
                        || (version_id == default_version_id() && req.version_id().is_none()))
            })
            .then_output(move || output.clone())
    }

    pub(crate) fn sqs_expectation() -> Rule {
        mock!(aws_sdk_sqs::Client::receive_message)
            .match_requests(|req| req.queue_url() == Some("url"))
            .then_output(expected_receive_message)
    }

    pub(crate) fn mock_sqs(rules: &[Rule]) -> SQSClient {
        SQSClient::new(mock_client!(aws_sdk_sqs, RuleMode::MatchAny, rules))
    }

    pub(crate) fn mock_s3(rules: &[Rule]) -> S3Client {
        S3Client::new(mock_client!(aws_sdk_s3, RuleMode::MatchAny, rules))
    }

    pub(crate) fn expected_head_object() -> HeadObjectOutput {
        HeadObjectOutput::builder()
            .last_modified(
                primitives::DateTime::from_str("1970-01-01T00:00:00Z", DateTimeFormat::DateTime)
                    .unwrap(),
            )
            .storage_class(types::StorageClass::IntelligentTiering)
            .archive_status(types::ArchiveStatus::DeepArchiveAccess)
            .checksum_sha256(EXPECTED_SHA256)
            .build()
    }

    pub(crate) fn expected_get_object_tagging() -> GetObjectTaggingOutput {
        GetObjectTaggingOutput::builder()
            .set_tag_set(Some(vec![]))
            .build()
            .unwrap()
    }

    pub(crate) fn expected_put_object_tagging() -> PutObjectTaggingOutput {
        PutObjectTaggingOutput::builder().build()
    }

    pub(crate) fn s3_client_expectations() -> S3Client {
        mock_s3(&[
            head_expectation(EXPECTED_VERSION_ID.to_string(), expected_head_object()),
            put_tagging_expectation(
                EXPECTED_VERSION_ID.to_string(),
                expected_put_object_tagging(),
            ),
            get_tagging_expectation(
                EXPECTED_VERSION_ID.to_string(),
                expected_get_object_tagging(),
            ),
        ])
    }

    pub(crate) fn sqs_client_expectations() -> SQSClient {
        mock_sqs(&[sqs_expectation()])
    }

    pub(crate) fn expected_head_object_not_found() -> HeadObjectError {
        HeadObjectError::NotFound(NotFound::builder().build())
    }

    async fn test_collecter<'a>(config: &'a Config, database_client: &'a Client) -> Collecter<'a> {
        Collecter::new(
            mock_s3(&[]),
            database_client,
            expected_flat_events_simple(),
            config,
        )
    }

    fn expected_receive_message() -> ReceiveMessageOutput {
        ReceiveMessageOutput::builder()
            .messages(
                MessageBuilder::default()
                    .body(expected_event_record_simple(false))
                    .build(),
            )
            .build()
    }
}
