use chrono::{DateTime, ParseError, Utc};
use serde::{Deserialize, Serialize};
use crate::error::Error;
use crate::error::Error::DeserializeError;
use crate::error::Result;

pub mod sqs;
pub mod s3;
pub mod ingester;

#[derive(Debug, Serialize, Deserialize)]
#[serde(try_from = "S3EventMessage")]
/// Flattened AWS S3 events
pub struct FlatS3EventMessages(pub Vec<FlatS3EventMessage>);

/// A flattened AWS S3 record
#[derive(Debug, Serialize, Deserialize)]
pub struct FlatS3EventMessage {
    pub event_time: DateTime<Utc>,
    pub event_name: String,
    pub bucket: String,
    pub key: String,
    pub size: i32,
    pub e_tag: String,
    pub sequencer: Option<String>
}

/// The basic AWS S3 Event.
#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct S3EventMessage {
    #[serde(rename = "Records")]
    pub records: Vec<Record>,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Record {
    pub event_time: String,
    pub event_name: String,
    pub s3: S3Record,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct S3Record {
    pub bucket: BucketRecord,
    pub object: ObjectRecord,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct BucketRecord {
    pub name: String,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ObjectRecord {
    pub key: String,
    pub size: i32,
    pub e_tag: String,
    pub sequencer: Option<String>
}

impl TryFrom<S3EventMessage> for FlatS3EventMessages {
    type Error = Error;

    fn try_from(message: S3EventMessage) -> Result<Self> {
        Ok(FlatS3EventMessages(message.records.into_iter().map(|record| {
            let Record {
                event_time, event_name, s3
            } = record;

            let S3Record {
                bucket, object
            } = s3;

            let BucketRecord {
                name: bucket
            } = bucket;

            let ObjectRecord {
                key, size, e_tag, sequencer
            } = object;

            Ok(FlatS3EventMessage {
                event_time: event_time.parse().map_err(|err: ParseError| DeserializeError(err.to_string()))?, event_name, bucket, key, size, e_tag, sequencer
            })
        }).collect::<Result<Vec<FlatS3EventMessage>>>()?))
    }
}

impl From<Vec<FlatS3EventMessages>> for FlatS3EventMessages {
    fn from(messages: Vec<FlatS3EventMessages>) -> Self {
        FlatS3EventMessages(messages.into_iter().map(|message| message.0).flatten().collect())
    }
}