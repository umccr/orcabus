//! Handles S3 Inventory reports and converts them to events that can be ingested.
//!

use crate::events::aws::message::EventType::Created;
use crate::events::aws::{FlatS3EventMessage, FlatS3EventMessages, StorageClass};
use crate::uuid::UuidGenerator;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

/// An S3 inventory record.
#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "PascalCase")]
pub struct Record {
    bucket: String,
    key: String,
    version_id: Option<String>,
    size: Option<i64>,
    last_modified_date: Option<DateTime<Utc>>,
    e_tag: Option<String>,
    storage_class: Option<StorageClass>,
}

impl From<Vec<Record>> for FlatS3EventMessages {
    fn from(records: Vec<Record>) -> Self {
        Self(records.into_iter().map(|record| record.into()).collect())
    }
}

impl From<Record> for FlatS3EventMessages {
    fn from(record: Record) -> Self {
        Self(vec![record.into()])
    }
}

impl From<Record> for FlatS3EventMessage {
    fn from(record: Record) -> Self {
        let Record {
            bucket,
            key,
            version_id,
            size,
            last_modified_date,
            e_tag,
            storage_class,
        } = record;

        Self {
            s3_object_id: UuidGenerator::generate(),
            // We don't know when this object was created so there is no event time.
            event_time: None,
            bucket,
            key,
            size,
            e_tag,
            // Set this to the empty string so that any deleted events after this can bind to this
            // created event.
            sequencer: Some("".to_string()),
            version_id: version_id.unwrap_or_else(FlatS3EventMessage::default_version_id),
            storage_class,
            last_modified_date,
            sha256: None,
            // Anything in an inventory report is always a created event.
            event_type: Created,
            number_reordered: 0,
            number_duplicate_events: 0,
        }
    }
}
