//! Handles ingesting S3 storage events.
//!

use aws_sdk_s3::primitives::DateTime;
use aws_sdk_s3::types::{ArchiveStatus, StorageClass};

/// Ingest files from S3.
pub struct Ingester {}

// #[derive(Debug)]
// pub struct S3 {
//     pub id: i64, // TODO: Should be unsigned?
//     pub bucket: String,
//     pub key: String,
//     pub size: i64, // TODO: Another type than unsigned int for size?
//     /// Corresponds to Last-Modified HeadObject response.
//     pub last_modified: Option<DateTime>,
//     /// Corresponds to Content-Length HeadObject response.
//     pub content_length: i64,
//     /// Corresponds to ETag HeadObject response.
//     pub e_tag: Option<String>,
//     /// Corresponds to the x-amz-storage-class HeadObject response.
//     pub storage_class: Option<StorageClass>,
//     /// Corresponds to x-amz-archive-status HeadObject response.
//     pub archive_status: Option<ArchiveStatus>,
//
// }
