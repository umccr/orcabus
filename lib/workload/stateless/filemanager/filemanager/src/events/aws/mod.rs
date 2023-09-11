use crate::error::Error;
use crate::error::Error::DeserializeError;
use crate::error::Result;
use chrono::{DateTime, ParseError, Utc};
use serde::{Deserialize, Serialize};
use std::cmp::Ordering;
use std::collections::{BTreeSet, HashSet};

pub mod s3;
pub mod sqs;

#[derive(Debug, Serialize, Deserialize, Eq, PartialEq)]
#[serde(try_from = "S3EventMessage")]
/// Flattened AWS S3 events
pub struct FlatS3EventMessages(pub Vec<FlatS3EventMessage>);

impl FlatS3EventMessages {
    /// Create a flattened event messages vector.
    pub fn new(messages: Vec<FlatS3EventMessage>) -> Self {
        Self(messages)
    }

    /// Get the inner vector.
    pub fn into_inner(self) -> Vec<FlatS3EventMessage> {
        self.0
    }

    /// Rearrange these messages so that duplicates are removed events are in the correct
    /// order.
    pub fn sort_and_dedup(self) -> Self {
        let mut messages = self.into_inner();

        messages.sort();
        messages.dedup();

        Self(messages)
    }
}

impl Ord for FlatS3EventMessage {
    fn cmp(&self, other: &Self) -> Ordering {
        // If the sequencer values are present and the bucket and key are the same.
        if let (Some(self_sequencer), Some(other_sequencer)) =
            (self.sequencer.as_ref(), other.sequencer.as_ref())
        {
            if self.bucket == other.bucket && self.key == other.key {
                return (
                    &self.sequencer,
                    &self.event_time,
                    &self.event_name,
                    &self.bucket,
                    &self.key,
                    &self.size,
                    &self.e_tag,
                )
                    .cmp(&(
                        &other.sequencer,
                        &other.event_time,
                        &other.event_name,
                        &other.bucket,
                        &other.key,
                        &other.size,
                        &other.e_tag,
                    ));
            }
        }

        (
            &self.event_time,
            &self.event_name,
            &self.bucket,
            &self.key,
            &self.size,
            &self.e_tag,
            &self.sequencer,
        )
            .cmp(&(
                &other.event_time,
                &other.event_name,
                &other.bucket,
                &other.key,
                &other.size,
                &other.e_tag,
                &other.sequencer,
            ))
    }
}

impl PartialOrd for FlatS3EventMessage {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

/// A flattened AWS S3 record
#[derive(Debug, Serialize, Deserialize, Eq, PartialEq)]
pub struct FlatS3EventMessage {
    pub event_time: DateTime<Utc>,
    pub event_name: String,
    pub bucket: String,
    pub key: String,
    pub size: i32,
    pub e_tag: String,
    pub sequencer: Option<String>,
}

/// The basic AWS S3 Event.
#[derive(Debug, Serialize, Deserialize, Eq, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct S3EventMessage {
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
    pub size: i32,
    pub e_tag: String,
    pub sequencer: Option<String>,
}

impl TryFrom<S3EventMessage> for FlatS3EventMessages {
    type Error = Error;

    fn try_from(message: S3EventMessage) -> Result<Self> {
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
                        sequencer,
                    } = object;

                    Ok(FlatS3EventMessage {
                        event_time: event_time
                            .parse()
                            .map_err(|err: ParseError| DeserializeError(err.to_string()))?,
                        event_name,
                        bucket,
                        key,
                        size,
                        e_tag,
                        sequencer,
                    })
                })
                .collect::<Result<Vec<FlatS3EventMessage>>>()?,
        ))
    }
}

impl From<Vec<FlatS3EventMessages>> for FlatS3EventMessages {
    fn from(messages: Vec<FlatS3EventMessages>) -> Self {
        FlatS3EventMessages(
            messages
                .into_iter()
                .map(|message| message.0)
                .flatten()
                .collect(),
        )
    }
}
