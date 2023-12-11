use std::env;

use aws_config::BehaviorVersion;
use aws_sdk_s3::operation::head_object::{HeadObjectError, HeadObjectOutput};
use aws_sdk_s3::Client;
use chrono::{DateTime, NaiveDateTime, Utc};
use futures::future::join_all;
use tracing::trace;

use crate::error::Error::S3Error;
use crate::error::Result;
use crate::events::s3::{FlatS3EventMessage, FlatS3EventMessages, StorageClass};

/// A wrapper around an s3 client.
#[derive(Debug)]
pub struct S3 {
    s3_client: Client,
}

impl S3 {
    /// Create a new S3 client wrapper.
    pub fn new(s3_client: Client) -> Self {
        Self { s3_client }
    }

    /// Create with a default S3 client.
    pub async fn with_defaults() -> Result<Self> {
        let mut config = aws_config::defaults(BehaviorVersion::latest());

        if let Ok(endpoint) = env::var("ENDPOINT_URL") {
            trace!("Using endpoint {}", endpoint);
            config = config.endpoint_url(endpoint);
        }

        // TODO: path_style seems to have been deprecated?? Did we need this for something important?
        //
        // if let Ok(path_style) = env::var("FORCE_PATH_STYLE") {
        //     if let Ok(path_style) = path_style.parse::<bool>() {
        //         config = config.force_path_style(path_style);
        //     }
        // }

        Ok(Self {
            s3_client: Client::new(&config.load().await),
        })
    }

    /// Gets some S3 metadata from HEAD such as (creation/archival) timestamps and statuses
    pub async fn head(&self, key: &str, bucket: &str) -> Result<Option<HeadObjectOutput>> {
        let buckets = self.s3_client.list_buckets().send().await;
        trace!(buckets = ?buckets, "buckets");

        let head = self
            .s3_client
            .head_object()
            .bucket(bucket)
            .key(key)
            .send()
            .await;

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

    /// Process events and add header and datetime fields.
    pub async fn update_events(&self, events: FlatS3EventMessages) -> Result<FlatS3EventMessages> {
        Ok(FlatS3EventMessages(
            join_all(events.into_inner().into_iter().map(|event| async move {
                trace!(key = ?event.key, bucket = ?event.bucket, "updating event");

                // if let Some(head) = self.head(&event.key, &event.bucket).await? {
                //     trace!("Before headoject storage/datetime mod");
                //     let HeadObjectOutput {
                //         storage_class,
                //         last_modified,
                //         ..
                //     } = head;
                //     trace!("In the middle of updating event");
                //     event =
                //         event.with_storage_class(storage_class.and_then(StorageClass::from_aws));
                //     event = event.with_last_modified_date(Self::convert_datetime(last_modified));
                // }

                // trace!(key = ?event.key, bucket = ?event.bucket, "event updated");
 
                Ok(event)
            }))
            .await
            .into_iter()
            .collect::<Result<Vec<FlatS3EventMessage>>>()?,
        ))
    }
}
