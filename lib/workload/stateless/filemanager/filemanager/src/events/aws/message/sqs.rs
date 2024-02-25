use crate::error::Error;
use crate::error::Error::DeserializeError;
use crate::error::Result;
use crate::events::aws::EventType::{Created, Deleted, Other};
use crate::events::aws::{FlatS3EventMessage, FlatS3EventMessages};
use chrono::{DateTime, ParseError, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// An S3 event message received directly by settings up an SQS queue.
/// https://docs.aws.amazon.com/AmazonS3/latest/userguide/notification-content-structure.html
#[derive(Debug, Serialize, Deserialize, Eq, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct SQSEventMessage {
    #[serde(rename = "Records")]
    pub records: Vec<Record>,
}

#[derive(Debug, Serialize, Deserialize, Eq, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct Record {
    pub event_time: String,
    pub event_name: String,
    pub s3: S3Record,
}

#[derive(Debug, Serialize, Deserialize, Eq, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct S3Record {
    pub bucket: BucketRecord,
    pub object: ObjectRecord,
}

#[derive(Debug, Serialize, Deserialize, Eq, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct BucketRecord {
    pub name: String,
}

#[derive(Debug, Serialize, Deserialize, Eq, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ObjectRecord {
    pub key: String,
    pub size: Option<i32>,
    pub e_tag: Option<String>,
    pub version_id: Option<String>,
    pub sequencer: Option<String>,
}

impl TryFrom<SQSEventMessage> for FlatS3EventMessages {
    type Error = Error;

    fn try_from(message: SQSEventMessage) -> Result<Self> {
        Ok(FlatS3EventMessages(
            message
                .records
                .into_iter()
                .map(|record| {
                    let Record {
                        event_time,
                        event_name,
                        s3,
                    } = record;

                    let S3Record { bucket, object } = s3;

                    let BucketRecord { name: bucket } = bucket;

                    let ObjectRecord {
                        key,
                        size,
                        e_tag,
                        version_id,
                        sequencer,
                    } = object;

                    let event_time: DateTime<Utc> = event_time
                        .parse()
                        .map_err(|err: ParseError| DeserializeError(err.to_string()))?;

                    let event_type = if event_name.contains("ObjectCreated") {
                        Created
                    } else if event_name.contains("ObjectRemoved") {
                        Deleted
                    } else {
                        Other
                    };

                    Ok(FlatS3EventMessage {
                        s3_object_id: Uuid::new_v4(),
                        event_time: Some(event_time),
                        bucket,
                        key,
                        size,
                        e_tag,
                        sequencer,
                        version_id,
                        // Head field are fetched later.
                        storage_class: None,
                        last_modified_date: None,
                        event_type,
                        number_reordered: 0,
                        number_duplicate_events: 0,
                    })
                })
                .collect::<crate::error::Result<Vec<FlatS3EventMessage>>>()?,
        ))
    }
}
