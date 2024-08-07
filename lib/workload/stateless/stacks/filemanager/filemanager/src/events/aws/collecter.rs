//! Definition and implementation of the aws Collecter.
//!

use async_trait::async_trait;
use aws_sdk_s3::operation::head_object::HeadObjectOutput;
use aws_sdk_s3::primitives;
use aws_sdk_s3::types::StorageClass::Standard;
use chrono::{DateTime, Utc};
use futures::future::join_all;
use futures::TryFutureExt;
use mockall_double::double;
use tracing::{trace, warn};

#[double]
use crate::clients::aws::s3::Client;
#[double]
use crate::clients::aws::s3::Client as S3Client;
#[double]
use crate::clients::aws::sqs::Client as SQSClient;
use crate::env::Config;
use crate::error::Error::{DeserializeError, SQSError};
use crate::error::Result;
use crate::events::aws::{
    EventType, FlatS3EventMessage, FlatS3EventMessages, StorageClass, TransposedS3EventMessages,
};
use crate::events::{Collect, EventSource, EventSourceType};

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
    pub async fn build(self, raw_events: FlatS3EventMessages, config: &Config) -> Collecter<'_> {
        if let Some(s3_client) = self.s3_client {
            Collecter::new(s3_client, raw_events, config)
        } else {
            Collecter::new(S3Client::with_defaults().await, raw_events, config)
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
                    let events: Option<FlatS3EventMessages> = serde_json::from_str(body)
                        .map_err(|err| DeserializeError(err.to_string()))?;
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
    pub async fn build_receive(mut self, config: &Config) -> Result<Collecter> {
        let url = self.sqs_url.take();
        let url = Config::value_or_else(url.as_deref(), config.sqs_url())?;

        let client = self.sqs_client.take();
        if let Some(sqs_client) = &client {
            Ok(self
                .build(Self::receive(sqs_client, url).await?, config)
                .await)
        } else {
            Ok(self
                .build(
                    Self::receive(&SQSClient::with_defaults().await, url).await?,
                    config,
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
    client: Client,
    raw_events: FlatS3EventMessages,
    config: &'a Config,
    n_records: Option<usize>,
}

impl<'a> Collecter<'a> {
    /// Create a new collector.
    pub(crate) fn new(client: Client, raw_events: FlatS3EventMessages, config: &'a Config) -> Self {
        Self {
            client,
            raw_events,
            config,
            n_records: None,
        }
    }

    /// Get the inner values.
    pub fn into_inner(self) -> (Client, FlatS3EventMessages, &'a Config) {
        (self.client, self.raw_events, self.config)
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
    pub async fn head(client: &Client, key: &str, bucket: &str) -> Option<HeadObjectOutput> {
        client
            .head_object(key, bucket)
            .map_err(|err| {
                let err = err.into_service_error();
                warn!("Error received from HeadObject: {}", err);
                err
            })
            .await
            .ok()
    }

    /// Process events and add header and datetime fields.
    pub async fn update_events(
        client: &Client,
        events: FlatS3EventMessages,
    ) -> Result<FlatS3EventMessages> {
        Ok(FlatS3EventMessages(
            join_all(events.into_inner().into_iter().map(|mut event| async move {
                // No need to run this unnecessarily on removed events.
                match event.event_type {
                    EventType::Deleted | EventType::Other => return Ok(event),
                    _ => {}
                };

                trace!(key = ?event.key, bucket = ?event.bucket, "updating event");

                // Race condition: it's possible that an object gets deleted so quickly that it
                // occurs before calling head. This means that there may be cases where the storage
                // class and other fields are not known.
                if let Some(head) = Self::head(client, &event.key, &event.bucket).await {
                    trace!(head = ?head, "received head object output");

                    let HeadObjectOutput {
                        storage_class,
                        last_modified,
                        content_length,
                        e_tag,
                        checksum_sha256,
                        ..
                    } = head;

                    // S3 does not return a storage class for standard, which means this is the
                    // default. See https://docs.aws.amazon.com/AmazonS3/latest/API/API_HeadObject.html#API_HeadObject_ResponseSyntax
                    event = event
                        .update_storage_class(StorageClass::from_aws(
                            storage_class.unwrap_or(Standard),
                        ))
                        .update_last_modified_date(Self::convert_datetime(last_modified))
                        .update_size(content_length)
                        .update_e_tag(e_tag)
                        .update_sha256(checksum_sha256);
                }

                Ok(event)
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

#[async_trait]
impl<'a> Collect for Collecter<'a> {
    async fn collect(mut self) -> Result<EventSource> {
        let (client, events, config) = self.into_inner();

        let n_records = events.0.len();
        let events = events.sort_and_dedup();

        let events = Self::update_events(&client, events).await?;
        // Get only the known event types.
        let events = events.filter_known();

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
    use std::result;

    use aws_sdk_s3::error::SdkError;
    use aws_sdk_s3::operation::head_object::HeadObjectError;
    use aws_sdk_s3::primitives::{DateTimeFormat, SdkBody};
    use aws_sdk_s3::types;
    use aws_sdk_s3::types::error::NotFound;
    use aws_sdk_sqs::operation::receive_message::ReceiveMessageOutput;
    use aws_sdk_sqs::types::builders::MessageBuilder;
    use aws_smithy_runtime_api::client::orchestrator::HttpResponse;
    use aws_smithy_runtime_api::client::result::ServiceError;
    use mockall::predicate::eq;

    use crate::events::aws::tests::{
        expected_event_record_simple, expected_flat_events_simple, EXPECTED_SHA256,
    };
    use crate::events::aws::StorageClass::IntelligentTiering;

    use super::*;

    #[tokio::test]
    async fn receive() {
        let mut sqs_client = SQSClient::default();

        set_sqs_client_expectations(&mut sqs_client);

        let events = CollecterBuilder::receive(&sqs_client, "url").await.unwrap();

        let mut expected = expected_flat_events_simple();
        expected
            .0
            .iter_mut()
            .zip(&events.0)
            .for_each(|(expected_event, event)| {
                // The object id will be different for each event.
                expected_event.s3_object_id = event.s3_object_id;
                expected_event.object_id = event.object_id;
                expected_event.public_id = event.public_id;
            });

        assert_eq!(events, expected);
    }

    #[tokio::test]
    async fn build_receive() {
        let mut sqs_client = SQSClient::default();
        let mut s3_client = S3Client::default();

        set_sqs_client_expectations(&mut sqs_client);
        set_s3_client_expectations(&mut s3_client, vec![|| Ok(expected_head_object())]);

        let events = CollecterBuilder::default()
            .with_sqs_client(sqs_client)
            .with_s3_client(s3_client)
            .with_sqs_url("url")
            .build_receive(&Default::default())
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

    #[tokio::test]
    async fn head() {
        let config = Default::default();
        let mut collecter = test_collecter(&config).await;

        set_s3_client_expectations(&mut collecter.client, vec![|| Ok(expected_head_object())]);

        let result = Collecter::head(&collecter.client, "key", "bucket").await;
        assert_eq!(result, Some(expected_head_object()));
    }

    #[tokio::test]
    async fn head_not_found() {
        let config = Default::default();
        let mut collecter = test_collecter(&config).await;

        set_s3_client_expectations(
            &mut collecter.client,
            vec![|| Err(expected_head_object_not_found())],
        );

        let result = Collecter::head(&collecter.client, "key", "bucket").await;
        assert!(result.is_none());
    }

    #[tokio::test]
    async fn update_events() {
        let config = Default::default();
        let mut collecter = test_collecter(&config).await;

        let events = expected_flat_events_simple().sort_and_dedup();

        set_s3_client_expectations(&mut collecter.client, vec![|| Ok(expected_head_object())]);

        let mut result = Collecter::update_events(&collecter.client, events)
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

    #[tokio::test]
    async fn collect() {
        let config = Default::default();
        let mut collecter = test_collecter(&config).await;

        set_s3_client_expectations(&mut collecter.client, vec![|| Ok(expected_head_object())]);

        let result = collecter.collect().await.unwrap().into_inner().0;

        assert_collected_events(result);
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

    pub(crate) fn set_s3_client_expectations<F>(client: &mut Client, expectations: Vec<F>)
    where
        F: Fn() -> result::Result<HeadObjectOutput, SdkError<HeadObjectError>> + Send + 'static,
    {
        let client = client
            .expect_head_object()
            .with(eq("key"), eq("bucket"))
            .times(expectations.len());

        for expectation in expectations {
            client.returning(move |_, _| expectation());
        }
    }

    pub(crate) fn set_sqs_client_expectations(sqs_client: &mut SQSClient) {
        sqs_client
            .expect_receive_message()
            .with(eq("url"))
            .times(1)
            .returning(move |_| Ok(expected_receive_message()));
    }

    pub(crate) fn expected_head_object() -> HeadObjectOutput {
        HeadObjectOutput::builder()
            .last_modified(
                primitives::DateTime::from_str("1970-01-01T00:00:00Z", DateTimeFormat::DateTime)
                    .unwrap(),
            )
            .storage_class(types::StorageClass::IntelligentTiering)
            .checksum_sha256(EXPECTED_SHA256)
            .build()
    }

    pub(crate) fn expected_head_object_not_found() -> SdkError<HeadObjectError> {
        SdkError::ServiceError(
            ServiceError::builder()
                .source(HeadObjectError::NotFound(NotFound::builder().build()))
                .raw(HttpResponse::new(404.try_into().unwrap(), SdkBody::empty()))
                .build(),
        )
    }

    async fn test_collecter(config: &Config) -> Collecter<'_> {
        Collecter::new(Client::default(), expected_flat_events_simple(), config)
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
