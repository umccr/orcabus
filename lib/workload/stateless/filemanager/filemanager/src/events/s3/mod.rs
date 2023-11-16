use std::cmp::Ordering;

use aws_sdk_s3::types::StorageClass as AwsStorageClass;
use chrono::{DateTime, ParseError, Utc};
use serde::{Deserialize, Serialize};
use sqlx::postgres::{PgHasArrayType, PgTypeInfo};
use uuid::Uuid;

use crate::error::Error;
use crate::error::Error::DeserializeError;
use crate::error::Result;

pub mod collect;
pub mod s3_client;
pub mod sqs_client;

/// A wrapper around AWS storage types with sqlx support.
#[derive(Debug, Eq, PartialEq, sqlx::Type)]
#[sqlx(type_name = "storage_class")]
pub enum StorageClass {
    DeepArchive,
    Glacier,
    GlacierIr,
    IntelligentTiering,
    OnezoneIa,
    Outposts,
    ReducedRedundancy,
    Snow,
    Standard,
    StandardIa,
}

impl PgHasArrayType for StorageClass {
    fn array_type_info() -> PgTypeInfo {
        PgTypeInfo::with_name("_storage_class")
    }
}

impl StorageClass {
    /// Convert from the AWS storage class type to the filemanager storage class.
    pub fn from_aws(storage_class: AwsStorageClass) -> Option<Self> {
        match storage_class {
            AwsStorageClass::DeepArchive => Some(Self::DeepArchive),
            AwsStorageClass::Glacier => Some(Self::Glacier),
            AwsStorageClass::GlacierIr => Some(Self::GlacierIr),
            AwsStorageClass::IntelligentTiering => Some(Self::IntelligentTiering),
            AwsStorageClass::OnezoneIa => Some(Self::OnezoneIa),
            AwsStorageClass::Outposts => Some(Self::Outposts),
            AwsStorageClass::ReducedRedundancy => Some(Self::ReducedRedundancy),
            AwsStorageClass::Snow => Some(Self::Snow),
            AwsStorageClass::Standard => Some(Self::Standard),
            AwsStorageClass::StandardIa => Some(Self::StandardIa),
            _ => None,
        }
    }
}

/// AWS S3 events with fields transposed
#[derive(Debug, Eq, PartialEq, Default)]
pub struct TransposedS3EventMessages {
    pub object_ids: Vec<Uuid>,
    pub event_times: Vec<DateTime<Utc>>,
    pub event_names: Vec<String>,
    pub buckets: Vec<String>,
    pub keys: Vec<String>,
    pub sizes: Vec<i32>,
    pub e_tags: Vec<String>,
    pub sequencers: Vec<Option<String>>,
    pub portal_run_ids: Vec<String>,
    pub storage_classes: Vec<Option<StorageClass>>,
    pub last_modified_dates: Vec<Option<DateTime<Utc>>>,
}

impl TransposedS3EventMessages {
    /// Create a new transposed S3 event messages vector with the given capacity.
    pub fn with_capacity(capacity: usize) -> Self {
        Self {
            object_ids: Vec::with_capacity(capacity),
            event_times: Vec::with_capacity(capacity),
            event_names: Vec::with_capacity(capacity),
            buckets: Vec::with_capacity(capacity),
            keys: Vec::with_capacity(capacity),
            sizes: Vec::with_capacity(capacity),
            e_tags: Vec::with_capacity(capacity),
            sequencers: Vec::with_capacity(capacity),
            portal_run_ids: Vec::with_capacity(capacity),
            storage_classes: Vec::with_capacity(capacity),
            last_modified_dates: Vec::with_capacity(capacity),
        }
    }

    /// Push an S3 event message.
    pub fn push(&mut self, message: FlatS3EventMessage) {
        let FlatS3EventMessage {
            object_id,
            event_time,
            event_name,
            bucket,
            key,
            size,
            e_tag,
            sequencer,
            portal_run_id,
            storage_class,
            last_modified_date,
        } = message;

        self.object_ids.push(object_id);
        self.event_times.push(event_time);
        self.event_names.push(event_name);
        self.buckets.push(bucket);
        self.keys.push(key);
        self.sizes.push(size);
        self.e_tags.push(e_tag);
        self.sequencers.push(sequencer);
        self.portal_run_ids.push(portal_run_id);
        self.storage_classes.push(storage_class);
        self.last_modified_dates.push(last_modified_date);
    }
}

impl From<FlatS3EventMessages> for TransposedS3EventMessages {
    fn from(messages: FlatS3EventMessages) -> Self {
        let messages = messages.into_inner();
        let capacity = messages.len();

        messages.into_iter().fold(
            TransposedS3EventMessages::with_capacity(capacity),
            |mut acc, message| {
                acc.push(message);
                acc
            },
        )
    }
}

/// Group by event types.
#[derive(Debug)]
pub struct Events {
    pub object_created: TransposedS3EventMessages,
    pub object_removed: TransposedS3EventMessages,
    pub other: TransposedS3EventMessages,
}

impl From<FlatS3EventMessages> for Events {
    fn from(messages: FlatS3EventMessages) -> Self {
        let mut object_created = FlatS3EventMessages::default();
        let mut object_removed = FlatS3EventMessages::default();
        let mut other = FlatS3EventMessages::default();

        messages.into_inner().into_iter().for_each(|message| {
            if message.event_name.contains("ObjectCreated") {
                object_created.0.push(message);
            } else if message.event_name.contains("ObjectRemoved") {
                object_removed.0.push(message);
            } else {
                other.0.push(message);
            }
        });

        Self {
            object_created: TransposedS3EventMessages::from(object_created),
            object_removed: TransposedS3EventMessages::from(object_removed),
            other: TransposedS3EventMessages::from(other),
        }
    }
}

/// Flattened AWS S3 events
#[derive(Debug, Deserialize, Eq, PartialEq, Default)]
#[serde(try_from = "S3EventMessage")]
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
                    self_sequencer,
                    &self.event_time,
                    &self.event_name,
                    &self.bucket,
                    &self.key,
                    &self.size,
                    &self.e_tag,
                )
                    .cmp(&(
                        other_sequencer,
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
#[derive(Debug, Eq, PartialEq)]
pub struct FlatS3EventMessage {
    pub object_id: Uuid,
    pub event_time: DateTime<Utc>,
    pub event_name: String,
    pub bucket: String,
    pub key: String,
    pub size: i32,
    pub e_tag: String,
    pub sequencer: Option<String>,
    pub portal_run_id: String,
    pub storage_class: Option<StorageClass>,
    pub last_modified_date: Option<DateTime<Utc>>,
}

impl FlatS3EventMessage {
    /// Update the storage class.
    pub fn with_storage_class(mut self, storage_class: Option<StorageClass>) -> Self {
        self.storage_class = storage_class;
        self
    }

    /// Update the last modified date.
    pub fn with_last_modified_date(mut self, last_modified_date: Option<DateTime<Utc>>) -> Self {
        self.last_modified_date = last_modified_date;
        self
    }
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

                    let event_time: DateTime<Utc> = event_time
                        .parse()
                        .map_err(|err: ParseError| DeserializeError(err.to_string()))?;

                    let object_id = Uuid::new_v4();
                    let portal_run_id =
                        event_time.format("%Y%m%d").to_string() + &object_id.to_string()[..8];

                    Ok(FlatS3EventMessage {
                        object_id,
                        event_time,
                        event_name,
                        bucket,
                        key,
                        size,
                        e_tag,
                        sequencer,
                        portal_run_id,
                        // Head field are optionally fetched later.
                        storage_class: None,
                        last_modified_date: None,
                    })
                })
                .collect::<Result<Vec<FlatS3EventMessage>>>()?,
        ))
    }
}

impl From<Vec<FlatS3EventMessages>> for FlatS3EventMessages {
    fn from(messages: Vec<FlatS3EventMessages>) -> Self {
        FlatS3EventMessages(messages.into_iter().flat_map(|message| message.0).collect())
    }
}
