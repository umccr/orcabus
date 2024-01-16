//! Convert S3 events for the database.
//!

use std::cmp::Ordering;

use aws_sdk_s3::types::StorageClass as AwsStorageClass;
use chrono::{DateTime, ParseError, Utc};
use itertools::Itertools;
use serde::{Deserialize, Serialize};
use sqlx::postgres::{PgHasArrayType, PgTypeInfo};
use uuid::Uuid;

use crate::error::Error;
use crate::error::Error::DeserializeError;
use crate::error::Result;
use crate::events::aws::EventType::{Created, Other, Removed};

pub mod collecter;
pub mod collector_builder;

/// A wrapper around AWS storage types with sqlx support.
#[derive(Debug, Eq, PartialEq, PartialOrd, Ord, Clone, sqlx::Type)]
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

/// AWS S3 events with fields transposed. Transposed events are used because this matches the
/// unnest structure when inserting events into the database. This is convenient to do here so that
/// the database structs do not have to perform this conversion.
#[derive(Debug, Eq, PartialEq, Default, Clone)]
pub struct TransposedS3EventMessages {
    pub object_ids: Vec<Uuid>,
    pub event_times: Vec<DateTime<Utc>>,
    pub event_names: Vec<String>,
    pub buckets: Vec<String>,
    pub keys: Vec<String>,
    pub sizes: Vec<Option<i64>>,
    pub e_tags: Vec<Option<String>>,
    pub sequencers: Vec<Option<String>>,
    pub portal_run_ids: Vec<String>,
    pub storage_classes: Vec<Option<StorageClass>>,
    pub last_modified_dates: Vec<Option<DateTime<Utc>>>,
}

impl TransposedS3EventMessages {
    /// Create a new transposed S3 event messages vector with the given capacity.
    /// TODO: There was a S3 messaging spec about how long those fields are supposed to be?
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
            ..
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

        messages
            .into_inner()
            .into_iter()
            .for_each(|message| match message.event_type {
                Created => {
                    object_created.0.push(message);
                }
                Removed => {
                    object_removed.0.push(message);
                }
                Other => {
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

    /// Rearrange messages so that duplicates are removed events are in the correct
    /// order. Note that the standard `PartialEq`, `Eq`, `PartialOrd` and `Ord` are not
    /// directly used because the `PartialOrd` is not consistent with `PartialEq`. Namely,
    /// when ordering events, the event time is taken into account, however it is not taken
    /// into account for event equality.
    pub fn sort_and_dedup(self) -> Self {
        self.dedup().sort()
    }

    /// Equality is implemented so that for the same bucket and key, the event is considered the same if the
    /// sequencer, event name, and version matches. Crucially, this means that events with different event times
    /// may be considered the same. Events may arrive at different times, but represent the same event. This matches
    /// the logic in this example:
    /// https://github.com/aws-samples/amazon-s3-endedupe/blob/bd906412c2b4ca26eee6312e3ac99120790b9de9/endedupe/app.py#L79-L83
    pub fn dedup(self) -> Self {
        let mut messages = self.into_inner();

        Self(
            messages
                .into_iter()
                .unique_by(|value| {
                    (
                        value.sequencer.clone(),
                        value.event_name.clone(),
                        value.bucket.clone(),
                        value.key.clone(),
                        value.size,
                        value.e_tag.clone(),
                        // Note, `last_modified` and `storage_class` are always `None` at this point anyway so don't need
                        // to be considered.
                    )
                })
                .collect(),
        )
    }

    /// Ordering is implemented so that the sequencer values are considered when the bucket and the
    /// key are the same.
    ///
    /// Unlike the `dedup` function, this implementation does consider the event time. This means that events
    /// will be ingested in event time order if the sequencer condition is not met.
    pub fn sort(self) -> Self {
        let mut messages = self.into_inner();

        messages.sort();
        messages.sort_by(|a, b| {
            if let (Some(a_sequencer), Some(b_sequencer)) =
                (a.sequencer.as_ref(), b.sequencer.as_ref())
            {
                if a.bucket == b.bucket && a.key == b.key {
                    return (
                        a_sequencer,
                        &a.event_time,
                        &a.event_name,
                        &a.bucket,
                        &a.key,
                        &a.size,
                        &a.e_tag,
                        &a.storage_class,
                        &a.last_modified_date,
                    )
                        .cmp(&(
                            b_sequencer,
                            &b.event_time,
                            &b.event_name,
                            &b.bucket,
                            &b.key,
                            &b.size,
                            &b.e_tag,
                            &b.storage_class,
                            &b.last_modified_date,
                        ));
                }
            }

            (
                &a.event_time,
                &a.sequencer,
                &a.event_name,
                &a.bucket,
                &a.key,
                &a.size,
                &a.e_tag,
                &a.storage_class,
                &a.last_modified_date,
            )
                .cmp(&(
                    &b.event_time,
                    &b.sequencer,
                    &b.event_name,
                    &b.bucket,
                    &b.key,
                    &b.size,
                    &b.e_tag,
                    &b.storage_class,
                    &b.last_modified_date,
                ))
        });

        Self(messages)
    }
}

#[derive(Debug, Eq, PartialEq, Ord, PartialOrd)]
pub enum EventType {
    Created,
    Removed,
    Other,
}

/// A flattened AWS S3 record
#[derive(Debug, Eq, PartialEq, Ord, PartialOrd)]
pub struct FlatS3EventMessage {
    pub sequencer: Option<String>,
    pub event_name: String,
    pub bucket: String,
    pub key: String,
    pub size: Option<i64>,
    pub e_tag: Option<String>,
    pub storage_class: Option<StorageClass>,
    pub last_modified_date: Option<DateTime<Utc>>,
    pub object_id: Uuid,
    pub event_time: DateTime<Utc>,
    pub portal_run_id: String,
    pub event_type: EventType,
}

impl FlatS3EventMessage {
    /// Update the storage class if not None.`
    pub fn update_storage_class(mut self, storage_class: Option<StorageClass>) -> Self {
        storage_class
            .into_iter()
            .for_each(|storage_class| self.storage_class = Some(storage_class));
        self
    }

    /// Update the last modified date if not None.
    pub fn update_last_modified_date(mut self, last_modified_date: Option<DateTime<Utc>>) -> Self {
        last_modified_date
            .into_iter()
            .for_each(|last_modified_date| self.last_modified_date = Some(last_modified_date));
        self
    }

    /// Update the size if not None.
    pub fn update_size(mut self, size: Option<i64>) -> Self {
        size.into_iter().for_each(|size| self.size = Some(size));
        self
    }

    /// Update the e_tag if not None.
    pub fn update_e_tag(mut self, e_tag: Option<String>) -> Self {
        e_tag.into_iter().for_each(|e_tag| self.e_tag = Some(e_tag));
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
    pub size: Option<i64>,
    pub e_tag: Option<String>,
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

                    let event_type = if event_name.contains("ObjectCreated") {
                        Created
                    } else if event_name.contains("ObjectRemoved") {
                        Removed
                    } else {
                        Other
                    };

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
                        // Head field are fetched later.
                        storage_class: None,
                        last_modified_date: None,
                        event_type,
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

#[cfg(test)]
pub(crate) mod tests {
    use crate::events::aws::{Events, FlatS3EventMessage, FlatS3EventMessages, S3EventMessage};
    use chrono::{DateTime, Utc};
    use serde_json::json;

    pub(crate) const EXPECTED_SEQUENCER_CREATED: &str = "0055AED6DCD90281E5"; // pragma: allowlist secret
    pub(crate) const EXPECTED_SEQUENCER_DELETED: &str = "0055AED6DCD90281E6"; // pragma: allowlist secret
    pub(crate) const EXPECTED_E_TAG: &str = "d41d8cd98f00b204e9800998ecf8427e"; // pragma: allowlist secret

    #[test]
    fn test_flat_events() {
        let result = expected_flat_events();
        let mut result = result.into_inner().into_iter();

        let first = result.next().unwrap();
        assert_flat_s3_event(
            first,
            "ObjectRemoved:Delete",
            EXPECTED_SEQUENCER_DELETED,
            None,
        );

        let second = result.next().unwrap();
        assert_flat_s3_event(
            second,
            "ObjectCreated:Put",
            EXPECTED_SEQUENCER_CREATED,
            Some(0),
        );

        let third = result.next().unwrap();
        assert_flat_s3_event(
            third,
            "ObjectCreated:Put",
            EXPECTED_SEQUENCER_CREATED,
            Some(0),
        );
    }

    #[test]
    fn test_sort_and_dedup() {
        let result = expected_flat_events().sort_and_dedup();
        let mut result = result.into_inner().into_iter();

        let first = result.next().unwrap();
        assert_flat_s3_event(
            first,
            "ObjectCreated:Put",
            EXPECTED_SEQUENCER_CREATED,
            Some(0),
        );

        let second = result.next().unwrap();
        assert_flat_s3_event(
            second,
            "ObjectRemoved:Delete",
            EXPECTED_SEQUENCER_DELETED,
            None,
        );
    }

    fn assert_flat_s3_event(
        event: FlatS3EventMessage,
        event_name: &str,
        sequencer: &str,
        size: Option<i64>,
    ) {
        assert_eq!(event.event_time, DateTime::<Utc>::default());
        assert_eq!(event.event_name, event_name);
        assert_eq!(event.bucket, "bucket");
        assert_eq!(event.key, "key");
        assert_eq!(event.size, size);
        assert_eq!(event.e_tag, Some(EXPECTED_E_TAG.to_string())); // pragma: allowlist secret
        assert_eq!(event.sequencer, Some(sequencer.to_string()));
        assert!(event.portal_run_id.starts_with("19700101"));
        assert_eq!(event.storage_class, None);
        assert_eq!(event.last_modified_date, None);
    }

    #[test]
    fn test_events() {
        let result = expected_events();

        assert_eq!(
            result.object_created.event_times[0],
            DateTime::<Utc>::default()
        );
        assert_eq!(result.object_created.event_names[0], "ObjectCreated:Put");
        assert_eq!(result.object_created.buckets[0], "bucket");
        assert_eq!(result.object_created.keys[0], "key");
        assert_eq!(result.object_created.sizes[0], Some(0));
        assert_eq!(
            result.object_created.e_tags[0],
            Some(EXPECTED_E_TAG.to_string())
        );
        assert_eq!(
            result.object_created.sequencers[0],
            Some(EXPECTED_SEQUENCER_CREATED.to_string())
        );
        assert!(result.object_created.portal_run_ids[0].starts_with("19700101"));
        assert_eq!(result.object_created.storage_classes[0], None);
        assert_eq!(result.object_created.last_modified_dates[0], None);

        assert_eq!(
            result.object_removed.event_times[0],
            DateTime::<Utc>::default()
        );
        assert_eq!(result.object_removed.event_names[0], "ObjectRemoved:Delete");
        assert_eq!(result.object_removed.buckets[0], "bucket");
        assert_eq!(result.object_removed.keys[0], "key");
        assert_eq!(result.object_removed.sizes[0], None);
        assert_eq!(
            result.object_removed.e_tags[0],
            Some(EXPECTED_E_TAG.to_string())
        );
        assert_eq!(
            result.object_removed.sequencers[0],
            Some(EXPECTED_SEQUENCER_DELETED.to_string())
        );
        assert!(result.object_removed.portal_run_ids[0].starts_with("19700101"));
        assert_eq!(result.object_removed.storage_classes[0], None);
        assert_eq!(result.object_removed.last_modified_dates[0], None);
    }

    pub(crate) fn expected_flat_events() -> FlatS3EventMessages {
        let events: S3EventMessage = serde_json::from_str(&expected_event_record()).unwrap();
        events.try_into().unwrap()
    }

    pub(crate) fn expected_events() -> Events {
        let events = expected_flat_events().sort_and_dedup();
        events.try_into().unwrap()
    }

    pub(crate) fn expected_event_record() -> String {
        let object = json!({
            "eventVersion": "2.2",
            "eventSource": "aws:s3",
            "awsRegion": "us-west-2",
            "userIdentity": {
                "principalId": "123456789012"
            },
            "requestParameters": {
                "sourceIPAddress": "127.0.0.1"
            },
            "responseElements": {
            "x-amz-request-id": "C3D13FE58DE4C810", // pragma: allowlist secret
                "x-amz-id-2": "FMyUVURIY8/IgAtTv8xRjskZQpcIZ9KG4V5Wp6S7S/JRWeUWerMUE5JgHvANOjpD" // pragma: allowlist secret
            },
            "s3": {
                "s3SchemaVersion": "1.0",
                "configurationId": "testConfigRule",
                "bucket": {
                   "name": "bucket",
                   "ownerIdentity": {
                      "principalId":"123456789012"
                   },
                   "arn": "arn:aws:s3:::bucket"
                },
                "object": {
                   "key": "key",
                   "size": 0,
                   "eTag": EXPECTED_E_TAG,
                   "versionId": "096fKKXTRTtl3on89fVO.nfljtsv6qko",
                   "sequencer": EXPECTED_SEQUENCER_CREATED
                }
            },
            "glacierEventData": {
                "restoreEventData": {
                   "lifecycleRestorationExpiryTime": "1970-01-01T00:00:00.000Z",
                   "lifecycleRestoreStorageClass": "Standard"
                }
            }
        });

        let mut object_created = object.clone();
        object_created["eventTime"] = json!("1970-01-01T00:00:00.000Z");
        object_created["eventName"] = json!("ObjectCreated:Put");
        object_created["s3"] = json!({
            "s3SchemaVersion": "1.0",
            "configurationId": "testConfigRule",
            "bucket": {
               "name": "bucket",
               "ownerIdentity": {
                  "principalId":"123456789012"
               },
               "arn": "arn:aws:s3:::bucket"
            },
            "object": {
               "key": "key",
               "size": 0,
               "eTag": EXPECTED_E_TAG,
               "versionId": "096fKKXTRTtl3on89fVO.nfljtsv6qko",
               "sequencer": EXPECTED_SEQUENCER_CREATED
            }
        });

        let object_created_duplicate = object_created.clone();

        let mut object_removed = object;
        object_removed["eventTime"] = json!("1970-01-01T00:00:00.000Z");
        object_removed["eventName"] = json!("ObjectRemoved:Delete");
        object_removed["s3"] = json!({
            "s3SchemaVersion": "1.0",
            "configurationId": "testConfigRule",
            "bucket": {
               "name": "bucket",
               "ownerIdentity": {
                  "principalId":"123456789012"
               },
               "arn": "arn:aws:s3:::bucket"
            },
            "object": {
               "key": "key",
                // ObjectRemoved::Delete does not have a size, even though this isn't documented
                // anywhere.
               "eTag": EXPECTED_E_TAG,
               "versionId": "096fKKXTRTtl3on89fVO.nfljtsv6qko",
               "sequencer": EXPECTED_SEQUENCER_DELETED
            }
        });

        json!({
           "Records": [
                object_removed,
                object_created,
                object_created_duplicate,
           ]
        })
        .to_string()
    }
}
