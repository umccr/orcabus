//! Database logic for AWS events.
//!

use crate::events::aws::StorageClass as InternalStorageClass;
use aws_sdk_s3::types::StorageClass;
use chrono::{DateTime, Utc};
use uuid::Uuid;

pub mod ingester;

#[cfg(feature = "migrate")]
pub mod migration;

/// An S3 object which matches the s3 object schema.
#[derive(Debug, Clone)]
pub struct CloudObject {
    pub storage_class: Option<StorageClass>,
}

#[derive(Debug)]
pub struct S3ObjectTable {
    pub s3_object_id: Uuid,
    pub object_id: Uuid,
    pub bucket: String,
    pub key: String,
    pub created_date: DateTime<Utc>,
    pub deleted_date: Option<DateTime<Utc>>,
    pub last_modified_date: Option<DateTime<Utc>>,
    pub e_tag: Option<String>,
    pub storage_class: Option<InternalStorageClass>,
    pub version_id: Option<String>,
    pub created_sequencer: Option<String>,
    pub deleted_sequencer: Option<String>,
    pub number_reordered: i32,
    pub number_duplicate_events: i32,
}
