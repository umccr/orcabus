//! Handles parsing raw S3 event messages and converting them for the database.
//!

use aws_sdk_s3::types::StorageClass as AwsStorageClass;
use chrono::{DateTime, Utc};
use itertools::{izip, Itertools};
use serde::Deserialize;
use sqlx::postgres::{PgHasArrayType, PgTypeInfo};
use uuid::Uuid;

use message::EventMessage;

use crate::events::aws::message::EventType;
use crate::events::aws::EventType::{Created, Deleted, Other};
use crate::uuid::UuidGenerator;

pub mod collecter;
pub mod message;

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
    pub s3_object_ids: Vec<Uuid>,
    pub event_times: Vec<Option<DateTime<Utc>>>,
    pub buckets: Vec<String>,
    pub keys: Vec<String>,
    pub version_ids: Vec<String>,
    pub sizes: Vec<Option<i64>>,
    pub e_tags: Vec<Option<String>>,
    pub sha256s: Vec<Option<String>>,
    pub sequencers: Vec<Option<String>>,
    pub storage_classes: Vec<Option<StorageClass>>,
    pub last_modified_dates: Vec<Option<DateTime<Utc>>>,
    pub event_types: Vec<EventType>,
}

impl TransposedS3EventMessages {
    /// Create a new transposed S3 event messages vector with the given capacity.
    /// TODO: There was a S3 messaging spec about how long those fields are supposed to be?
    pub fn with_capacity(capacity: usize) -> Self {
        Self {
            s3_object_ids: Vec::with_capacity(capacity),
            event_times: Vec::with_capacity(capacity),
            buckets: Vec::with_capacity(capacity),
            keys: Vec::with_capacity(capacity),
            version_ids: Vec::with_capacity(capacity),
            sizes: Vec::with_capacity(capacity),
            e_tags: Vec::with_capacity(capacity),
            sha256s: Vec::with_capacity(capacity),
            sequencers: Vec::with_capacity(capacity),
            storage_classes: Vec::with_capacity(capacity),
            last_modified_dates: Vec::with_capacity(capacity),
            event_types: Vec::with_capacity(capacity),
        }
    }

    /// Push an S3 event message.
    pub fn push(&mut self, message: FlatS3EventMessage) {
        let FlatS3EventMessage {
            s3_object_id,
            event_time,
            bucket,
            key,
            size,
            version_id,
            e_tag,
            sha256,
            sequencer,
            storage_class,
            last_modified_date,
            event_type,
            ..
        } = message;

        self.s3_object_ids.push(s3_object_id);
        self.event_times.push(event_time);
        self.buckets.push(bucket);
        self.keys.push(key);
        self.version_ids.push(version_id);
        self.sizes.push(size);
        self.e_tags.push(e_tag);
        self.sha256s.push(sha256);
        self.sequencers.push(sequencer);
        self.storage_classes.push(storage_class);
        self.last_modified_dates.push(last_modified_date);
        self.event_types.push(event_type);
    }
}

/// Conversion from flat events to transposed events.
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

/// Conversion from transposed events to flat events. This is useful for processing events returned by the database
/// after updating out of order events.
impl From<TransposedS3EventMessages> for FlatS3EventMessages {
    fn from(messages: TransposedS3EventMessages) -> Self {
        let zip = izip!(
            messages.s3_object_ids,
            messages.event_times,
            messages.buckets,
            messages.keys,
            messages.version_ids,
            messages.sizes,
            messages.e_tags,
            messages.sha256s,
            messages.sequencers,
            messages.storage_classes,
            messages.last_modified_dates,
            messages.event_types
        )
        .map(
            |(
                s3_object_id,
                event_time,
                bucket,
                key,
                version_id,
                size,
                e_tag,
                sha256,
                sequencer,
                storage_class,
                last_modified_date,
                event_type,
            )| {
                FlatS3EventMessage {
                    s3_object_id,
                    sequencer,
                    bucket,
                    key,
                    version_id,
                    size,
                    e_tag,
                    sha256,
                    storage_class,
                    last_modified_date,
                    event_time,
                    event_type,
                    number_reordered: 0,
                    number_duplicate_events: 0,
                }
            },
        );

        FlatS3EventMessages(zip.collect())
    }
}

/// Group by event types.
#[derive(Debug, Clone, Default)]
pub struct Events {
    pub object_created: TransposedS3EventMessages,
    pub object_deleted: TransposedS3EventMessages,
    pub other: TransposedS3EventMessages,
}

impl Events {
    /// Set the created objects.
    pub fn with_object_created(mut self, object_created: TransposedS3EventMessages) -> Self {
        self.object_created = object_created;
        self
    }

    /// Set the deleted objects.
    pub fn with_object_deleted(mut self, object_deleted: TransposedS3EventMessages) -> Self {
        self.object_deleted = object_deleted;
        self
    }

    /// Set the other events.
    pub fn with_other(mut self, other: TransposedS3EventMessages) -> Self {
        self.other = other;
        self
    }
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
                Deleted => {
                    object_removed.0.push(message);
                }
                Other => {
                    other.0.push(message);
                }
            });

        Self {
            object_created: TransposedS3EventMessages::from(object_created),
            object_deleted: TransposedS3EventMessages::from(object_removed),
            other: TransposedS3EventMessages::from(other),
        }
    }
}

/// Flattened AWS S3 events
#[derive(Debug, Deserialize, Eq, PartialEq, Default)]
#[serde(from = "EventMessage")]
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
        let messages = self.into_inner();

        Self(
            messages
                .into_iter()
                .unique_by(|value| {
                    (
                        value.sequencer.clone(),
                        value.event_type.clone(),
                        value.bucket.clone(),
                        value.key.clone(),
                        value.version_id.clone(),
                        // Note, `last_modified` and `storage_class` are always `None` at this point anyway so don't need
                        // to be considered. `size` and `e_tag` should be the same but are unimportant in deduplication.
                    )
                })
                .collect(),
        )
    }

    /// Ordering is implemented so that the sequencer values are considered when the bucket, the
    /// key and the version id are the same.
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
                if a.bucket == b.bucket
                    && a.key == b.key
                    && a.version_id == b.version_id
                    && a.event_type == b.event_type
                {
                    return (
                        a_sequencer,
                        &a.event_time,
                        &a.event_type,
                        &a.bucket,
                        &a.key,
                        &a.version_id,
                        &a.size,
                        &a.e_tag,
                        &a.sha256,
                        &a.storage_class,
                        &a.last_modified_date,
                    )
                        .cmp(&(
                            b_sequencer,
                            &b.event_time,
                            &b.event_type,
                            &b.bucket,
                            &b.key,
                            &b.version_id,
                            &b.size,
                            &b.e_tag,
                            &a.sha256,
                            &b.storage_class,
                            &b.last_modified_date,
                        ));
                }
            }

            (
                &a.event_time,
                &a.sequencer,
                &a.event_type,
                &a.bucket,
                &a.key,
                &a.version_id,
                &a.size,
                &a.e_tag,
                &a.sha256,
                &a.storage_class,
                &a.last_modified_date,
            )
                .cmp(&(
                    &b.event_time,
                    &b.sequencer,
                    &b.event_type,
                    &b.bucket,
                    &b.key,
                    &b.version_id,
                    &b.size,
                    &b.e_tag,
                    &a.sha256,
                    &b.storage_class,
                    &b.last_modified_date,
                ))
        });

        Self(messages)
    }
}

/// A flattened AWS S3 record
#[derive(Debug, Eq, PartialEq, Ord, PartialOrd, Clone, Default)]
pub struct FlatS3EventMessage {
    pub s3_object_id: Uuid,
    pub sequencer: Option<String>,
    pub bucket: String,
    pub key: String,
    pub version_id: String,
    pub size: Option<i64>,
    pub e_tag: Option<String>,
    pub sha256: Option<String>,
    pub storage_class: Option<StorageClass>,
    pub last_modified_date: Option<DateTime<Utc>>,
    pub event_time: Option<DateTime<Utc>>,
    pub event_type: EventType,
    pub number_reordered: i64,
    pub number_duplicate_events: i64,
}

impl FlatS3EventMessage {
    /// Create an event with a newly generated s3_object_id.
    pub fn new_with_generated_id() -> Self {
        Self::default().with_s3_object_id(UuidGenerator::generate())
    }

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

    /// Update the sha256 if not None.
    pub fn update_sha256(mut self, sha256: Option<String>) -> Self {
        sha256
            .into_iter()
            .for_each(|sha256| self.sha256 = Some(sha256));
        self
    }

    /// Set the bucket.
    pub fn with_s3_object_id(mut self, s3_object_id: Uuid) -> Self {
        self.s3_object_id = s3_object_id;
        self
    }

    /// Set the sequencer value.
    pub fn with_sequencer(mut self, sequencer: Option<String>) -> Self {
        self.sequencer = sequencer;
        self
    }

    /// Set the bucket.
    pub fn with_bucket(mut self, bucket: String) -> Self {
        self.bucket = bucket;
        self
    }

    /// Set the key.
    pub fn with_key(mut self, key: String) -> Self {
        self.key = key;
        self
    }

    /// Set the version id.
    pub fn with_version_id(mut self, version_id: String) -> Self {
        self.version_id = version_id;
        self
    }

    /// Set the version id.
    pub fn with_default_version_id(mut self) -> Self {
        self.version_id = Self::default_version_id();
        self
    }

    /// Set the size.
    pub fn with_size(mut self, size: Option<i64>) -> Self {
        self.size = size;
        self
    }

    /// Set the e_tag.
    pub fn with_e_tag(mut self, e_tag: Option<String>) -> Self {
        self.e_tag = e_tag;
        self
    }

    /// Set the storage class.
    pub fn with_storage_class(mut self, storage_class: Option<StorageClass>) -> Self {
        self.storage_class = storage_class;
        self
    }

    /// Set the last modified date.
    pub fn with_last_modified_date(mut self, last_modified_date: Option<DateTime<Utc>>) -> Self {
        self.last_modified_date = last_modified_date;
        self
    }

    /// Set the event time.
    pub fn with_event_time(mut self, event_time: Option<DateTime<Utc>>) -> Self {
        self.event_time = event_time;
        self
    }

    /// Set the event type.
    pub fn with_event_type(mut self, event_type: EventType) -> Self {
        self.event_type = event_type;
        self
    }

    pub fn default_version_id() -> String {
        "null".to_string()
    }
}

impl From<Vec<FlatS3EventMessages>> for FlatS3EventMessages {
    fn from(messages: Vec<FlatS3EventMessages>) -> Self {
        FlatS3EventMessages(messages.into_iter().flat_map(|message| message.0).collect())
    }
}

#[cfg(test)]
pub(crate) mod tests {
    use chrono::{DateTime, Utc};
    use serde_json::{json, Value};

    use crate::events::aws::message::Message;
    use crate::events::aws::{
        EventType, Events, FlatS3EventMessage, FlatS3EventMessages, TransposedS3EventMessages,
    };

    pub(crate) const EXPECTED_SEQUENCER_CREATED_ZERO: &str = "0055AED6DCD90281E3"; // pragma: allowlist secret
    pub(crate) const EXPECTED_SEQUENCER_CREATED_ONE: &str = "0055AED6DCD90281E4"; // pragma: allowlist secret
    pub(crate) const EXPECTED_NEW_SEQUENCER_ONE: &str = "0055AED6DCD90281E5"; // pragma: allowlist secret
    pub(crate) const EXPECTED_SEQUENCER_DELETED_ONE: &str = "0055AED6DCD90281E6"; // pragma: allowlist secret
    pub(crate) const EXPECTED_SEQUENCER_CREATED_TWO: &str = "0055AED6DCD90281E7"; // pragma: allowlist secret
    pub(crate) const EXPECTED_SEQUENCER_DELETED_TWO: &str = "0055AED6DCD90281E9"; // pragma: allowlist secret

    pub(crate) const EXPECTED_E_TAG: &str = "d41d8cd98f00b204e9800998ecf8427e"; // pragma: allowlist secret

    pub(crate) const EXPECTED_VERSION_ID: &str = "096fKKXTRTtl3on89fVO.nfljtsv6qko";
    pub(crate) const EXPECTED_SHA256: &str = "Y0sCextp4SQtQNU+MSs7SsdxD1W+gfKJtUlEbvZ3i+4="; // pragma: allowlist secret
    pub(crate) const EXPECTED_REQUEST_ID: &str = "C3D13FE58DE4C810"; // pragma: allowlist secret

    #[test]
    fn test_flat_events() {
        let result = expected_flat_events_simple();
        let mut result = result.into_inner().into_iter();

        let first = result.next().unwrap();
        assert_flat_s3_event(
            first,
            &EventType::Deleted,
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            None,
            EXPECTED_VERSION_ID.to_string(),
        );

        let second = result.next().unwrap();
        assert_flat_s3_event(
            second,
            &EventType::Created,
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            Some(0),
            EXPECTED_VERSION_ID.to_string(),
        );

        let third = result.next().unwrap();
        assert_flat_s3_event(
            third,
            &EventType::Created,
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            Some(0),
            EXPECTED_VERSION_ID.to_string(),
        );
    }

    #[test]
    fn test_sort_and_dedup() {
        let result = expected_flat_events_simple().sort_and_dedup();
        let mut result = result.into_inner().into_iter();

        let first = result.next().unwrap();
        assert_flat_s3_event(
            first,
            &EventType::Created,
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            Some(0),
            EXPECTED_VERSION_ID.to_string(),
        );

        let second = result.next().unwrap();
        assert_flat_s3_event(
            second,
            &EventType::Deleted,
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            None,
            EXPECTED_VERSION_ID.to_string(),
        );
    }

    #[test]
    fn test_sort_and_dedup_with_version_id() {
        let result = expected_flat_events_simple();

        let mut result = result.into_inner();
        result.push(
            expected_flat_events_simple()
                .into_inner()
                .first()
                .unwrap()
                .clone()
                .with_version_id("version_id".to_string()),
        );

        let result = FlatS3EventMessages(result).sort_and_dedup();
        let mut result = result.into_inner().into_iter();

        let first = result.next().unwrap();
        assert_flat_s3_event(
            first,
            &EventType::Created,
            Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()),
            Some(0),
            EXPECTED_VERSION_ID.to_string(),
        );

        let second = result.next().unwrap();
        assert_flat_s3_event(
            second,
            &EventType::Deleted,
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            None,
            EXPECTED_VERSION_ID.to_string(),
        );

        let third = result.next().unwrap();
        assert_flat_s3_event(
            third,
            &EventType::Deleted,
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            None,
            "version_id".to_string(),
        );
    }

    pub(crate) fn assert_flat_s3_event(
        event: FlatS3EventMessage,
        event_type: &EventType,
        sequencer: Option<String>,
        size: Option<i64>,
        version_id: String,
    ) {
        assert_eq!(event.event_time, Some(DateTime::<Utc>::default()));
        assert_eq!(&event.event_type, event_type);
        assert_eq!(event.bucket, "bucket");
        assert_eq!(event.key, "key");
        assert_eq!(event.version_id, version_id);
        assert_eq!(event.size, size);
        assert_eq!(event.e_tag, Some(EXPECTED_E_TAG.to_string()));
        assert_eq!(event.sequencer, sequencer);
        assert_eq!(event.storage_class, None);
        assert_eq!(event.last_modified_date, None);
    }

    fn assert_object(
        events: &TransposedS3EventMessages,
        position: usize,
        size: Option<i64>,
        bucket: &str,
        key: &str,
        sequencer: &str,
    ) {
        assert_eq!(events.buckets[position], bucket);
        assert_eq!(events.keys[position], key);
        assert_eq!(events.sizes[position], size);
        assert_eq!(
            events.version_ids[position],
            EXPECTED_VERSION_ID.to_string()
        );
        assert_eq!(events.e_tags[position], Some(EXPECTED_E_TAG.to_string()));
        assert_eq!(events.sequencers[position], Some(sequencer.to_string()));
        assert_eq!(events.storage_classes[position], None);
        assert_eq!(events.last_modified_dates[position], None);
    }

    #[test]
    fn test_events() {
        let result = expected_events_full();

        assert_object(
            &result.object_created,
            0,
            Some(0),
            "bucket",
            "key",
            EXPECTED_SEQUENCER_CREATED_ONE,
        );
        assert_object(
            &result.object_deleted,
            0,
            None,
            "bucket",
            "key",
            EXPECTED_SEQUENCER_DELETED_ONE,
        );

        assert_object(
            &result.object_created,
            1,
            Some(0),
            "bucket",
            "key",
            EXPECTED_SEQUENCER_CREATED_TWO,
        );
        assert_object(
            &result.object_deleted,
            1,
            None,
            "bucket",
            "key",
            EXPECTED_SEQUENCER_DELETED_TWO,
        );
    }

    fn expected_flat_events(records: String) -> FlatS3EventMessages {
        let events: Message = serde_json::from_str(&records).unwrap();
        events.into()
    }

    fn expected_events(records: String) -> Events {
        let events = expected_flat_events(records).sort_and_dedup();
        events.into()
    }

    pub(crate) fn expected_flat_events_simple() -> FlatS3EventMessages {
        expected_flat_events(expected_event_record_simple())
    }

    pub(crate) fn expected_events_simple() -> Events {
        expected_events(expected_event_record_simple())
    }

    pub(crate) fn expected_events_full() -> Events {
        expected_events(expected_event_record_full())
    }

    pub(crate) fn expected_event_record_simple() -> String {
        let mut records: Value = serde_json::from_str(&expected_event_record_full()).unwrap();

        records["Records"] = json!([
            records["Records"][0].clone(),
            records["Records"][1].clone(),
            records["Records"][2].clone(),
        ]);

        records.to_string()
    }

    /// https://docs.aws.amazon.com/AmazonS3/latest/userguide/ev-events.html
    pub(crate) fn expected_event_bridge_record() -> Value {
        json!({
            "version": "0",
            "id": "2ee9cc15-d022-99ea-1fb8-1b1bac4850f9",
            "detail-type": "Object Deleted",
            "source": "aws.s3",
            "account": "111122223333",
            "time": "1970-01-01T00:00:00.000Z",
            "region": "ca-central-1",
            "resources": [
                "arn:aws:s3:::bucket"
            ],
            "detail": {
                "version": "0",
                "bucket": {
                    "name": "bucket"
                },
                "object": {
                    "key": "key",
                    "etag": EXPECTED_E_TAG,
                    "version-id": EXPECTED_VERSION_ID,
                    "sequencer": EXPECTED_SEQUENCER_DELETED_ONE,
                },
                "request-id": EXPECTED_REQUEST_ID,
                "requester": "123456789012",
                "source-ip-address": "127.0.0.1",
                "reason": "DeleteObject",
                "deletion-type": "Delete Marker Created"
            }
        })
    }

    /// https://docs.aws.amazon.com/AmazonS3/latest/userguide/notification-content-structure.html
    pub(crate) fn expected_sqs_record() -> Value {
        json!({
            "eventVersion": "2.2",
            "eventSource": "aws:s3",
            "awsRegion": "us-west-2",
            "eventTime": "1970-01-01T00:00:00.000Z",
            "eventName": "ObjectRemoved:Delete",
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
                    "eTag": EXPECTED_E_TAG,
                    "versionId": EXPECTED_VERSION_ID,
                    "sequencer": EXPECTED_SEQUENCER_DELETED_ONE,
                }
            },
            "glacierEventData": {
                "restoreEventData": {
                   "lifecycleRestorationExpiryTime": "1970-01-01T00:00:00.000Z",
                   "lifecycleRestoreStorageClass": "Standard"
                }
            }
        })
    }

    pub(crate) fn expected_event_record_full() -> String {
        let object = expected_sqs_record();

        let mut object_created_one = object.clone();
        object_created_one["eventName"] = json!("ObjectCreated:Put");
        object_created_one["s3"]["object"]["sequencer"] = json!(EXPECTED_SEQUENCER_CREATED_ONE);
        object_created_one["s3"]["object"]["size"] = json!(0);

        let object_created_one_duplicate = object_created_one.clone();

        let mut object_removed_one = object.clone();
        object_removed_one["eventName"] = json!("ObjectRemoved:Delete");
        object_removed_one["s3"]["object"]["sequencer"] = json!(EXPECTED_SEQUENCER_DELETED_ONE);

        let mut object_created_two = object.clone();
        object_created_two["eventName"] = json!("ObjectCreated:Put");
        object_created_two["s3"]["object"]["size"] = json!(0);
        object_created_two["s3"]["object"]["sequencer"] = json!(EXPECTED_SEQUENCER_CREATED_TWO);

        let mut object_removed_two = object.clone();
        object_removed_two["eventName"] = json!("ObjectRemoved:Delete");
        object_removed_two["s3"]["object"]["sequencer"] = json!(EXPECTED_SEQUENCER_DELETED_TWO);

        let object_removed_two_duplicate = object_removed_two.clone();

        json!({
           "Records": [
                object_removed_one,
                object_created_one,
                object_created_one_duplicate,
                object_created_two,
                object_removed_two,
                object_removed_two_duplicate
           ]
        })
        .to_string()
    }
}
