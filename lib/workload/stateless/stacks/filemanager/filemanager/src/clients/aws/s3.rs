//! A mockable wrapper around the S3 client.
//!

use std::result;

use aws_sdk_s3 as s3;
use aws_sdk_s3::error::SdkError;
use aws_sdk_s3::operation::get_object::{GetObjectError, GetObjectOutput};
use aws_sdk_s3::operation::get_object_tagging::{GetObjectTaggingError, GetObjectTaggingOutput};
use aws_sdk_s3::operation::head_object::{HeadObjectError, HeadObjectOutput};
use aws_sdk_s3::operation::list_buckets::{ListBucketsError, ListBucketsOutput};
use aws_sdk_s3::operation::list_objects_v2::{ListObjectsV2Error, ListObjectsV2Output};
use aws_sdk_s3::operation::put_object_tagging::{PutObjectTaggingError, PutObjectTaggingOutput};
use aws_sdk_s3::presigning::{PresignedRequest, PresigningConfig};
use aws_sdk_s3::types::ChecksumMode::Enabled;
use aws_sdk_s3::types::Tagging;
use chrono::Duration;

use crate::clients::aws::config::Config;
use crate::events::aws::message::default_version_id;

/// Maximum number of iterations for list objects.
pub const MAX_LIST_ITERATIONS: usize = 1000000;

pub type Result<T, E> = result::Result<T, SdkError<E>>;

/// A wrapper around an S3 client which can be mocked.
#[derive(Debug, Clone)]
pub struct Client {
    inner: s3::Client,
}

/// Override settings related to response headers.
#[derive(Debug, Clone)]
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

    /// Execute the `ListObjectsV2` operation, and handle pagination to produce all possible
    /// records.
    pub async fn list_objects(
        &self,
        bucket: &str,
        prefix: Option<String>,
    ) -> Result<ListObjectsV2Output, ListObjectsV2Error> {
        let list = |token| async {
            self.inner
                .list_objects_v2()
                .bucket(bucket)
                .set_prefix(prefix.clone())
                .set_continuation_token(token)
                .send()
                .await
        };

        let mut result = list(None).await?;

        for _ in 0..MAX_LIST_ITERATIONS {
            if !result
                .is_truncated()
                .is_some_and(|is_truncated| is_truncated)
            {
                break;
            }

            let mut next = list(result.next_continuation_token).await?;

            next.contents
                .get_or_insert_default()
                .extend(result.contents.unwrap_or_default());
            next.common_prefixes
                .get_or_insert_default()
                .extend(result.common_prefixes.unwrap_or_default());
            next.key_count =
                Some(next.key_count.unwrap_or_default() + result.key_count.unwrap_or_default());
            next.max_keys =
                Some(next.max_keys.unwrap_or_default() + result.max_keys.unwrap_or_default());

            result = next;
        }

        Ok(result)
    }

    fn get_version_id(version_id: &str) -> Option<String> {
        if version_id == default_version_id() {
            None
        } else {
            Some(version_id.to_string())
        }
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
            .set_version_id(Self::get_version_id(version_id))
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
            .set_version_id(Self::get_version_id(version_id))
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
            .set_version_id(Self::get_version_id(version_id))
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
            .set_version_id(Self::get_version_id(version_id))
            .tagging(tagging)
            .send()
            .await
    }

    /// Execute the `GetObject` operation and generate a presigned url for the object.
    pub async fn presign_url(
        &self,
        key: &str,
        bucket: &str,
        version_id: Option<String>,
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
            .set_version_id(version_id)
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
