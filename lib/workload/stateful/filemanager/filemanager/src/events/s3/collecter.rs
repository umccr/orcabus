use crate::clients::s3::Client;
use crate::error::Error::S3Error;
use async_trait::async_trait;
use aws_sdk_s3::operation::head_object::{HeadObjectError, HeadObjectOutput};
use chrono::{DateTime, NaiveDateTime, Utc};
use futures::future::join_all;
use tracing::trace;

use crate::error::Result;
use crate::events::s3::{Events, FlatS3EventMessage, FlatS3EventMessages, StorageClass};
use crate::events::{Collect, EventType};

/// Collect raw events into the processed form which the database module accepts.
#[derive(Debug)]
pub struct Collector {
    client: Client,
    raw_events: FlatS3EventMessages,
}

impl Collector {
    /// Create a new collector.
    pub(crate) fn new(client: Client, raw_events: FlatS3EventMessages) -> Self {
        Self { client, raw_events }
    }

    /// Get the inner values.
    pub fn into_inner(self) -> (Client, FlatS3EventMessages) {
        (self.client, self.raw_events)
    }

    /// Converts an AWS datetime to a standard database format.
    pub fn convert_datetime(
        datetime: Option<aws_sdk_s3::primitives::DateTime>,
    ) -> Option<DateTime<Utc>> {
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
impl Collect for Collector {
    async fn collect(self) -> Result<EventType> {
        let (client, raw_events) = self.into_inner();
        let events = Self::update_events(&client, raw_events).await?;

        Ok(EventType::S3(Events::from(events)))
    }
}
