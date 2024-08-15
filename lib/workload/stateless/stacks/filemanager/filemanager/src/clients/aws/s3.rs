//! A mockable wrapper around the S3 client.
//!

use crate::clients::aws::config::Config;
use aws_sdk_s3 as s3;
use aws_sdk_s3::error::SdkError;
use aws_sdk_s3::operation::get_object::{GetObjectError, GetObjectOutput};
use aws_sdk_s3::operation::head_object::{HeadObjectError, HeadObjectOutput};
use aws_sdk_s3::operation::list_buckets::{ListBucketsError, ListBucketsOutput};
use aws_sdk_s3::presigning::{PresignedRequest, PresigningConfig};
use aws_sdk_s3::types::ChecksumMode::Enabled;
use chrono::Duration;
use mockall::automock;
use std::result;

pub type Result<T, E> = result::Result<T, SdkError<E>>;

/// A wrapper around an S3 client which can be mocked.
#[derive(Debug)]
pub struct Client {
    inner: s3::Client,
}

#[automock]
impl Client {
    /// Create a new S3 client.
    pub fn new(inner: s3::Client) -> Self {
        Self { inner }
    }

    /// Create an S3 client with default config.
    pub async fn with_defaults() -> Self {
        Self::new(s3::Client::new(&Config::with_defaults().await.load()))
    }

    /// Execute the `ListBuckets` operation.
    pub async fn list_buckets(&self) -> Result<ListBucketsOutput, ListBucketsError> {
        self.inner.list_buckets().send().await
    }

    /// Execute the `HeadObject` operation.
    pub async fn head_object(
        &self,
        key: &str,
        bucket: &str,
    ) -> Result<HeadObjectOutput, HeadObjectError> {
        self.inner
            .head_object()
            .checksum_mode(Enabled)
            .key(key)
            .bucket(bucket)
            .send()
            .await
    }

    /// Execute the `GetObject` operation.
    pub async fn get_object(
        &self,
        key: &str,
        bucket: &str,
    ) -> Result<GetObjectOutput, GetObjectError> {
        self.inner
            .get_object()
            .checksum_mode(Enabled)
            .key(key)
            .bucket(bucket)
            .send()
            .await
    }

    /// Execute the `GetObject` operation and generate a presigned url for the object.
    pub async fn presign_url(
        &self,
        key: &str,
        bucket: &str,
        response_content_disposition: &str,
        expires_in: Duration,
    ) -> Result<PresignedRequest, GetObjectError> {
        self.inner
            .get_object()
            .response_content_disposition(response_content_disposition)
            .checksum_mode(Enabled)
            .key(key)
            .bucket(bucket)
            .presigned(
                PresigningConfig::expires_in(
                    expires_in
                        .to_std()
                        .map_err(SdkError::construction_failure)?,
                )
                .map_err(SdkError::construction_failure)?,
            )
            .await
    }
}
