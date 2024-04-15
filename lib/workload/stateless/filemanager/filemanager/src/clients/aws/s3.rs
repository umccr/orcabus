//! A mockable wrapper around the S3 client.
//!

use std::result;

use aws_sdk_s3 as s3;
use aws_sdk_s3::error::SdkError;
use aws_sdk_s3::operation::head_object::{HeadObjectError, HeadObjectOutput};
use aws_sdk_s3::operation::list_buckets::{ListBucketsError, ListBucketsOutput};
use aws_sdk_s3::types::ChecksumMode::Enabled;
use mockall::automock;

use crate::clients::aws::config::Config;

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
}
