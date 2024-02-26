//! Database logic for AWS events.
//!

use aws_sdk_s3::types::StorageClass;

pub mod query;
pub mod ingester;

#[cfg(feature = "migrate")]
pub mod migration;

/// An S3 object which matches the s3 object schema.
#[derive(Debug, Clone)]
pub struct CloudObject {
    pub storage_class: Option<StorageClass>,
}
