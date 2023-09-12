pub mod ingester;

use aws_sdk_s3::types::StorageClass;

/// An S3 object which matches the s3 object schema.
#[derive(Debug, Clone)]
pub struct CloudObject {
    pub storage_class: Option<StorageClass>,
}
