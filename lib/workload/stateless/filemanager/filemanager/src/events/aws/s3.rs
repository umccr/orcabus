use crate::database::aws::CloudObject;
use crate::database::CloudObject::S3 as S3CloudObject;
use crate::database::Object;
use crate::error::Error::{ConfigError, S3Error};
use crate::error::Result;
use crate::events::aws::{BucketRecord, ObjectRecord, S3EventMessage, S3Record};
use crate::file::File;
use aws_sdk_s3::operation::head_object::{HeadObjectError, HeadObjectOutput};
use aws_sdk_s3::Client;
use chrono::{DateTime, NaiveDateTime, Utc};
use futures::future::join_all;

#[derive(Debug)]
pub struct S3 {
    s3_client: Client,
}

impl S3 {
    pub fn new(s3_client: Client) -> Self {
        Self { s3_client }
    }

    pub async fn with_default_client() -> Result<Self> {
        let config = aws_config::from_env()
            .endpoint_url(
                std::env::var("ENDPOINT_URL").map_err(|err| ConfigError(err.to_string()))?,
            )
            .load()
            .await;

        Ok(Self {
            s3_client: Client::new(&config),
        })
    }

    /// Gets some S3 metadata from HEAD such as (creation/archival) timestamps and statuses
    pub async fn head(&self, key: &str, bucket: &str) -> Result<Option<HeadObjectOutput>> {
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
}
