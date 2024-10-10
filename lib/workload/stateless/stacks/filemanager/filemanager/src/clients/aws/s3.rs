//! A mockable wrapper around the S3 client.
//!

use std::result;

use aws_sdk_s3 as s3;
use aws_sdk_s3::error::SdkError;
use aws_sdk_s3::operation::get_object::{GetObjectError, GetObjectOutput};
use aws_sdk_s3::operation::get_object_tagging::{GetObjectTaggingError, GetObjectTaggingOutput};
use aws_sdk_s3::operation::head_object::{HeadObjectError, HeadObjectOutput};
use aws_sdk_s3::operation::list_buckets::{ListBucketsError, ListBucketsOutput};
use aws_sdk_s3::operation::put_object_tagging::{PutObjectTaggingError, PutObjectTaggingOutput};
use aws_sdk_s3::presigning::{PresignedRequest, PresigningConfig};
use aws_sdk_s3::types::ChecksumMode::Enabled;
use aws_sdk_s3::types::Tagging;
use chrono::Duration;
use mockall::automock;

use crate::clients::aws::config::Config;

pub type Result<T, E> = result::Result<T, SdkError<E>>;

/// A wrapper around an S3 client which can be mocked.
#[derive(Debug)]
pub struct Client {
    inner: s3::Client,
}

/// Override settings related to response headers.
#[derive(Debug)]
pub struct ResponseHeaders {
    content_disposition: String,
    content_type: Option<String>,
    content_encoding: Option<String>,
}

impl ResponseHeaders {
    /// Create a new `ResponseHeaders` config.
    pub fn new(
        content_disposition: String,
        content_type: Option<String>,
        content_encoding: Option<String>,
    ) -> Self {
        Self {
            content_disposition,
            content_type,
            content_encoding,
        }
    }

    /// Get the content disposition.
    pub fn content_disposition(&self) -> &str {
        &self.content_disposition
    }

    /// Get the content type.
    pub fn content_type(&self) -> Option<&str> {
        self.content_type.as_deref()
    }

    /// Get the content encoding.
    pub fn content_encoding(&self) -> Option<&str> {
        self.content_encoding.as_deref()
    }
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
        version_id: &str,
    ) -> Result<HeadObjectOutput, HeadObjectError> {
        self.inner
            .head_object()
            .checksum_mode(Enabled)
            .key(key)
            .bucket(bucket)
            .version_id(version_id)
            .send()
            .await
    }

    /// Execute the `GetObject` operation.
    pub async fn get_object(
        &self,
        key: &str,
        bucket: &str,
        version_id: &str,
    ) -> Result<GetObjectOutput, GetObjectError> {
        self.inner
            .get_object()
            .checksum_mode(Enabled)
            .key(key)
            .bucket(bucket)
            .version_id(version_id)
            .send()
            .await
    }

    /// Execute the `GetObjectTagging` operation.
    pub async fn get_object_tagging(
        &self,
        key: &str,
        bucket: &str,
        version_id: &str,
    ) -> Result<GetObjectTaggingOutput, GetObjectTaggingError> {
        self.inner
            .get_object_tagging()
            .key(key)
            .bucket(bucket)
            .version_id(version_id)
            .send()
            .await
    }

    /// Execute the `PutObjectTagging` operation.
    pub async fn put_object_tagging(
        &self,
        key: &str,
        bucket: &str,
        version_id: &str,
        tagging: Tagging,
    ) -> Result<PutObjectTaggingOutput, PutObjectTaggingError> {
        self.inner
            .put_object_tagging()
            .key(key)
            .bucket(bucket)
            .version_id(version_id)
            .tagging(tagging)
            .send()
            .await
    }

    /// Execute the `GetObject` operation and generate a presigned url for the object.
    pub async fn presign_url(
        &self,
        key: &str,
        bucket: &str,
        version_id: &str,
        response_headers: ResponseHeaders,
        expires_in: Duration,
    ) -> Result<PresignedRequest, GetObjectError> {
        self.inner
            .get_object()
            .response_content_disposition(response_headers.content_disposition)
            .set_response_content_type(response_headers.content_type)
            .set_response_content_encoding(response_headers.content_encoding)
            .key(key)
            .bucket(bucket)
            .version_id(version_id)
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
