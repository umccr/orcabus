#[double]
use crate::clients::s3::Client;
use crate::error::Error::S3Error;
use async_trait::async_trait;
use aws_sdk_s3::operation::head_object::{HeadObjectError, HeadObjectOutput};
use aws_sdk_s3::primitives;
use chrono::{DateTime, NaiveDateTime, Utc};
use futures::future::join_all;
use mockall_double::double;
use tracing::trace;

use crate::error::Result;
use crate::events::s3::{Events, FlatS3EventMessage, FlatS3EventMessages, StorageClass};
use crate::events::{Collect, EventType};

/// Collect raw events into the processed form which the database module accepts.
#[derive(Debug)]
pub struct Collecter {
    client: Client,
    raw_events: FlatS3EventMessages,
}

impl Collecter {
    /// Create a new collector.
    pub(crate) fn new(client: Client, raw_events: FlatS3EventMessages) -> Self {
        Self { client, raw_events }
    }

    /// Get the inner values.
    pub fn into_inner(self) -> (Client, FlatS3EventMessages) {
        (self.client, self.raw_events)
    }

    /// Converts an AWS datetime to a standard database format.
    pub fn convert_datetime(datetime: Option<primitives::DateTime>) -> Option<DateTime<Utc>> {
        if let Some(head) = datetime {
            let date = NaiveDateTime::from_timestamp_opt(head.secs(), head.subsec_nanos())?;
            Some(DateTime::from_naive_utc_and_offset(date, Utc))
        } else {
            None
        }
    }

    /// Gets S3 metadata from HeadObject such as creation/archival timestamps and statuses.
    pub async fn head(
        client: &Client,
        key: &str,
        bucket: &str,
    ) -> Result<Option<HeadObjectOutput>> {
        let head = client.head_object(key, bucket).await;

        match head {
            Ok(head) => Ok(Some(head)),
            Err(err) => {
                let err = err.into_service_error();
                if let HeadObjectError::NotFound(_) = err {
                    // Object not found, could be deleted.
                    Ok(None)
                } else {
                    // I.e: Cannot connect to server
                    Err(S3Error(err.to_string()))
                }
            }
        }
    }

    /// Process events and add header and datetime fields.
    pub async fn update_events(
        client: &Client,
        events: FlatS3EventMessages,
    ) -> Result<FlatS3EventMessages> {
        Ok(FlatS3EventMessages(
            join_all(events.into_inner().into_iter().map(|mut event| async move {
                trace!(key = ?event.key, bucket = ?event.bucket, "updating event");

                if let Some(head) = Self::head(client, &event.key, &event.bucket).await? {
                    let HeadObjectOutput {
                        storage_class,
                        last_modified,
                        ..
                    } = head;

                    event =
                        event.with_storage_class(storage_class.and_then(StorageClass::from_aws));
                    event = event.with_last_modified_date(Self::convert_datetime(last_modified));
                }

                Ok(event)
            }))
            .await
            .into_iter()
            .collect::<Result<Vec<FlatS3EventMessage>>>()?,
        ))
    }
}

#[async_trait]
impl Collect for Collecter {
    async fn collect(self) -> Result<EventType> {
        let (client, raw_events) = self.into_inner();
        let raw_events = raw_events.sort_and_dedup();

        let events = Self::update_events(&client, raw_events).await?;

        Ok(EventType::S3(Events::from(events)))
    }
}

#[cfg(test)]
pub(crate) mod tests {
    use crate::events::s3::collecter::Collecter;
    use crate::events::s3::tests::expected_flat_events;
    use crate::events::s3::StorageClass::Standard;
    use aws_sdk_s3::error::SdkError;
    use aws_sdk_s3::primitives::{DateTimeFormat, SdkBody};
    use aws_sdk_s3::types;
    use aws_sdk_s3::types::error::NotFound;
    use aws_smithy_runtime_api::client::orchestrator::HttpResponse;
    use aws_smithy_runtime_api::client::result::ServiceError;
    use chrono::{DateTime, Utc};
    use mockall::predicate::eq;

    use super::*;

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
        let mut collecter = test_collecter().await;

        set_s3_client_expectations(&mut collecter.client, 1);

        let result = Collecter::head(&collecter.client, "key", "bucket")
            .await
            .unwrap();
        assert_eq!(result, Some(expected_head_object()));
    }

    #[tokio::test]
    async fn head_not_found() {
        let mut collecter = test_collecter().await;

        collecter
            .client
            .expect_head_object()
            .with(eq("key"), eq("bucket"))
            .times(1)
            .returning(move |_, _| {
                Err(SdkError::ServiceError(
                    ServiceError::builder()
                        .source(HeadObjectError::NotFound(NotFound::builder().build()))
                        .raw(HttpResponse::new(404.try_into().unwrap(), SdkBody::empty()))
                        .build(),
                ))
            });

        let result = Collecter::head(&collecter.client, "key", "bucket")
            .await
            .unwrap();
        assert!(result.is_none());
    }

    #[tokio::test]
    async fn update_events() {
        let mut collecter = test_collecter().await;

        let events = expected_flat_events().sort_and_dedup();

        set_s3_client_expectations(&mut collecter.client, 2);

        let mut result = Collecter::update_events(&collecter.client, events)
            .await
            .unwrap()
            .into_inner()
            .into_iter();

        let first = result.next().unwrap();
        assert_eq!(first.storage_class, Some(Standard));
        assert_eq!(first.last_modified_date, Some(Default::default()));

        let second = result.next().unwrap();
        assert_eq!(second.storage_class, Some(Standard));
        assert_eq!(second.last_modified_date, Some(Default::default()));
    }

    #[tokio::test]
    async fn collect() {
        let mut collecter = test_collecter().await;

        set_s3_client_expectations(&mut collecter.client, 2);

        let result = collecter.collect().await.unwrap();

        assert_collected_events(result);
    }

    pub(crate) fn assert_collected_events(result: EventType) {
        assert!(matches!(result, EventType::S3(_)));

        match result {
            EventType::S3(events) => {
                assert_eq!(events.object_created.storage_classes[0], Some(Standard));
                assert_eq!(
                    events.object_created.last_modified_dates[0],
                    Some(Default::default())
                );

                assert_eq!(events.object_removed.storage_classes[0], Some(Standard));
                assert_eq!(
                    events.object_removed.last_modified_dates[0],
                    Some(Default::default())
                );
            }
        }
    }

    pub(crate) fn set_s3_client_expectations(client: &mut Client, times: usize) {
        client
            .expect_head_object()
            .with(eq("key"), eq("bucket"))
            .times(times)
            .returning(move |_, _| Ok(expected_head_object()));
    }

    fn expected_head_object() -> HeadObjectOutput {
        HeadObjectOutput::builder()
            .last_modified(
                primitives::DateTime::from_str("1970-01-01T00:00:00Z", DateTimeFormat::DateTime)
                    .unwrap(),
            )
            .storage_class(types::StorageClass::Standard)
            .build()
    }

    async fn test_collecter() -> Collecter {
        Collecter::new(Client::default(), expected_flat_events())
    }
}
