//! Raw event message definitions from AWS S3, either through EventBridge or SQS directly.
//!

use crate::database::entities::sea_orm_active_enums::Reason;
use crate::events::aws::{FlatS3EventMessage, FlatS3EventMessages};
use crate::uuid::UuidGenerator;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use strum::{EnumCount, FromRepr};

/// The type of S3 event.
#[derive(
    Debug, Default, Eq, PartialEq, Ord, PartialOrd, Clone, Hash, sqlx::Type, FromRepr, EnumCount,
)]
#[sqlx(type_name = "event_type")]
pub enum EventType {
    #[default]
    Created,
    Deleted,
    Other,
}

/// Data for converting from S3 events to the internal filemanager event type.
#[derive(Debug)]
pub struct EventTypeData {
    pub event_type: String,
    pub deletion_type: Option<String>,
    pub reason: Option<String>,
}

impl EventTypeData {
    /// Create a new event type data.
    pub fn new(event_type: String, deletion_type: Option<String>, reason: Option<String>) -> Self {
        Self {
            event_type,
            deletion_type,
            reason,
        }
    }

    /// Convert this data into the parsed type.
    ///
    /// Created events include events that are triggered by APIs like PutObject or CopyObject.
    /// They also include restore events (including restore expired), and lifecycle storage
    /// class transitions. This is because for all these events the object remains in S3 and
    /// it's metadata can be read.
    ///
    /// Deleted events include events that are triggered by APIs like DeleteObject, or lifecycle
    /// expire events. This is because for these events, the object can no longer be accessed in S3.
    pub fn into_parsed(self) -> EventTypeParsed {
        match &self.event_type {
            // Regular created event.
            e if e.contains("Object Created") || e.contains("ObjectCreated") => {
                EventTypeParsed::new(EventType::Created, false, self.reason_for_created())
            }
            // Restore complete.
            e if e.contains("Object Restore Completed")
                || e.contains("ObjectRestore:Completed") =>
            {
                EventTypeParsed::new(EventType::Created, false, Reason::Restored)
            }
            // Restore expired.
            e if e.contains("Object Restore Expired") || e.contains("ObjectRestore:Delete") => {
                EventTypeParsed::new(EventType::Created, false, Reason::RestoreExpired)
            }
            // Storage class changed.
            e if e.contains("Object Storage Class Changed")
                || e.contains("Object Access Tier Changed")
                || e.contains("LifecycleTransition")
                || e.contains("IntelligentTiering") =>
            {
                EventTypeParsed::new(EventType::Created, false, Reason::StorageClassChanged)
            }
            // Delete marker created event.
            e if (e.contains("Object Deleted")
                && self
                    .deletion_type
                    .as_ref()
                    .is_some_and(|d| d.contains("Delete Marker Created")))
                || e.contains("ObjectRemoved:DeleteMarkerCreated")
                || e.contains("LifecycleExpiration:DeleteMarkerCreated") =>
            {
                EventTypeParsed::new(EventType::Deleted, true, self.reason_for_deleted())
            }
            // Regular deleted event.
            e if e.contains("Object Deleted")
                || e.contains("ObjectRemoved")
                || e.contains("LifecycleExpiration") =>
            {
                EventTypeParsed::new(EventType::Deleted, false, self.reason_for_deleted())
            }
            // Anything else.
            _ => EventTypeParsed::new(EventType::Other, false, Reason::Unknown),
        }
    }

    /// Get the reason for a created event. This does not check if the event is a created event.
    pub fn reason_for_created(&self) -> Reason {
        if self.event_type.contains("Put")
            || self
                .reason
                .as_ref()
                .is_some_and(|r| r.contains("PutObject"))
        {
            Reason::CreatedPut
        } else if self.event_type.contains("Post")
            || self
                .reason
                .as_ref()
                .is_some_and(|r| r.contains("PostObject"))
        {
            Reason::CreatedPost
        } else if self.event_type.contains("Copy")
            || self
                .reason
                .as_ref()
                .is_some_and(|r| r.contains("CopyObject"))
        {
            Reason::CreatedCopy
        } else if self.event_type.contains("CompleteMultipartUpload")
            || self
                .reason
                .as_ref()
                .is_some_and(|r| r.contains("CompleteMultipartUpload"))
        {
            Reason::CreatedCompleteMultipartUpload
        } else {
            Reason::Unknown
        }
    }

    /// Get the reason for a deleted event. This does not check if the event is a deleted event.
    pub fn reason_for_deleted(&self) -> Reason {
        if self.event_type.contains("LifecycleExpiration")
            || self
                .reason
                .as_ref()
                .is_some_and(|r| r.contains("Lifecycle Expiration"))
        {
            Reason::DeletedLifecycle
        } else if self.event_type.contains("Delete")
            || self
                .reason
                .as_ref()
                .is_some_and(|r| r.contains("DeleteObject"))
        {
            Reason::Deleted
        } else {
            Reason::Unknown
        }
    }
}

/// The parsed event type with parsed information including the delete marker and reason.
#[derive(Debug)]
pub struct EventTypeParsed {
    pub event_type: EventType,
    pub is_delete_marker: bool,
    pub reason: Reason,
}

impl EventTypeParsed {
    /// Create a new event type with a delete marker flag and reason.
    pub fn new(event_type: EventType, is_delete_marker: bool, reason: Reason) -> Self {
        Self {
            event_type,
            is_delete_marker,
            reason,
        }
    }
}

impl From<EventTypeData> for EventTypeParsed {
    fn from(event_type: EventTypeData) -> Self {
        event_type.into_parsed()
    }
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(untagged)]
pub enum EventMessage {
    EventBridge(Record),
    SQS(Message),
}

impl From<EventMessage> for FlatS3EventMessages {
    fn from(message: EventMessage) -> Self {
        match message {
            EventMessage::EventBridge(record) => record.into(),
            EventMessage::SQS(message) => message.into(),
        }
    }
}

/// An S3 event message generated by an SQS queue or EventBridge. Serde rename and alias attributes
/// allow supporting both message types.
///
/// E.g.
/// https://docs.aws.amazon.com/AmazonS3/latest/userguide/notification-content-structure.html
/// https://docs.aws.amazon.com/AmazonS3/latest/userguide/ev-events.html
#[derive(Debug, Serialize, Deserialize, Eq, PartialEq)]
#[serde(rename_all = "kebab-case")]
pub struct Message {
    #[serde(alias = "Records")]
    pub records: Vec<Record>,
}

/// The inner record to for a message.
#[derive(Debug, Serialize, Deserialize, Eq, PartialEq)]
#[serde(rename_all = "kebab-case")]
pub struct Record {
    #[serde(alias = "eventTime")]
    pub time: DateTime<Utc>,
    #[serde(alias = "eventName")]
    pub detail_type: String,
    #[serde(alias = "s3")]
    pub detail: S3Record,
}

/// The detail of a message.
#[derive(Debug, Serialize, Deserialize, Eq, PartialEq)]
#[serde(rename_all = "kebab-case")]
pub struct S3Record {
    pub bucket: Bucket,
    pub object: Object,
    pub deletion_type: Option<String>,
    pub reason: Option<String>,
}

/// The bucket name in a message.
#[derive(Debug, Serialize, Deserialize, Eq, PartialEq)]
#[serde(rename_all = "kebab-case")]
pub struct Bucket {
    pub name: String,
}

/// The object information of a message.
#[derive(Debug, Serialize, Deserialize, Eq, PartialEq)]
#[serde(rename_all = "kebab-case")]
pub struct Object {
    pub key: String,
    pub size: Option<i64>,
    #[serde(alias = "eTag")]
    pub etag: Option<String>,
    #[serde(alias = "versionId")]
    pub version_id: Option<String>,
    pub sequencer: Option<String>,
}

impl From<Record> for FlatS3EventMessage {
    fn from(record: Record) -> Self {
        let Record {
            time,
            detail_type,
            detail,
        } = record;

        let S3Record {
            bucket,
            object,
            deletion_type,
            reason,
        } = detail;

        let Bucket { name: bucket } = bucket;

        let Object {
            key,
            size,
            etag,
            version_id,
            sequencer,
        } = object;

        let EventTypeParsed {
            event_type,
            is_delete_marker,
            reason,
        } = EventTypeParsed::from(EventTypeData::new(detail_type, deletion_type, reason));

        Self {
            s3_object_id: UuidGenerator::generate(),
            event_time: Some(time),
            bucket,
            key,
            size,
            e_tag: etag.map(quote_e_tag),
            sequencer,
            version_id: version_id.unwrap_or_else(default_version_id),
            // Head fields are fetched later.
            storage_class: None,
            last_modified_date: None,
            sha256: None,
            // This represents the current state only if the event is a created event.
            is_current_state: event_type == EventType::Created,
            event_type,
            is_delete_marker,
            reason,
            archive_status: None,
            ingest_id: None,
            attributes: None,
            number_duplicate_events: 0,
            number_reordered: 0,
        }
    }
}

impl From<Record> for FlatS3EventMessages {
    fn from(record: Record) -> Self {
        FlatS3EventMessages(vec![record.into()])
    }
}

impl From<Message> for FlatS3EventMessages {
    fn from(message: Message) -> Self {
        FlatS3EventMessages(
            message
                .records
                .into_iter()
                .fold(vec![], |mut flattened, record| {
                    flattened.extend(FlatS3EventMessages::from(record).into_inner());
                    flattened
                }),
        )
    }
}

/// Quote an e_tag if it has not already been quoted. This doesn't check the
/// validity of an e_tag, it only applies quoting if it is missing.
pub fn quote_e_tag(mut e_tag: String) -> String {
    if !e_tag.starts_with('"') && !e_tag.starts_with("W/\"") {
        e_tag.insert(0, '"');
    }

    if !e_tag.ends_with('"') || e_tag == "\"" || e_tag == "W/\"" {
        e_tag.push('"');
    }

    e_tag
}

/// The default version id.
pub fn default_version_id() -> String {
    "null".to_string()
}

#[cfg(test)]
mod tests {
    use serde_json::{json, Value};

    use crate::events::aws::message::quote_e_tag;
    use crate::events::aws::message::EventType::Created;
    use crate::events::aws::tests::{
        assert_flat_s3_event, expected_event_bridge_record,
        expected_event_bridge_record_delete_marker, expected_sqs_record, EXPECTED_E_TAG,
        EXPECTED_REQUEST_ID, EXPECTED_SEQUENCER_DELETED_ONE, EXPECTED_VERSION_ID,
    };
    use crate::events::aws::EventType::Deleted;
    use crate::events::aws::FlatS3EventMessages;

    #[test]
    fn test_e_tag_quoting() {
        // e_tag is already valid.
        assert_eq!(quote_e_tag("\"e_tag\"".to_string()), "\"e_tag\"");
        assert_eq!(quote_e_tag("W/\"e_tag\"".to_string()), "W/\"e_tag\"");
        assert_eq!(quote_e_tag("\"\"".to_string()), "\"\"");
        assert_eq!(quote_e_tag("W/\"\"".to_string()), "W/\"\"");

        // No quoting present on e_tag.
        assert_eq!(quote_e_tag("e_tag".to_string()), "\"e_tag\"");
        assert_eq!(quote_e_tag("".to_string()), "\"\"");

        // Partial quoting present on e_tag.
        assert_eq!(quote_e_tag("\"e_tag".to_string()), "\"e_tag\"");
        assert_eq!(quote_e_tag("e_tag\"".to_string()), "\"e_tag\"");
        assert_eq!(quote_e_tag("W/\"e_tag".to_string()), "W/\"e_tag\"");

        // Single quote character e_tag.
        assert_eq!(quote_e_tag("\"".to_string()), "\"\"");
        assert_eq!(quote_e_tag("W/\"".to_string()), "W/\"\"");
    }

    #[test]
    fn deserialize_large_size() {
        let message = format!(
            r#"{{
                "version": "0",
                "id": "2ee9cc15-d022-99ea-1fb8-1b1bac4850f9",
                "detail-type": "Object Created",
                "source": "aws.s3",
                "account": "111122223333",
                "time": "1970-01-01T00:00:00.000Z",
                "region": "ca-central-1",
                "resources": [
                    "arn:aws:s3:::bucket"
                ],
                "detail": {{
                    "version": "0",
                    "bucket": {{
                        "name": "bucket"
                    }},
                    "object": {{
                        "key": "key",
                        "size": {},
                        "etag": "{EXPECTED_E_TAG}",
                        "sequencer": "{EXPECTED_SEQUENCER_DELETED_ONE}"
                    }},
                    "request-id": "{EXPECTED_REQUEST_ID}",
                    "requester": "123456789012",
                    "source-ip-address": "127.0.0.1",
                    "reason": "CompleteMultipartUpload"
                }}
            }}"#,
            i64::MAX,
        );

        let result: FlatS3EventMessages = serde_json::from_str(&message).unwrap();
        let first_message = result.into_inner().first().unwrap().clone();

        assert_flat_s3_event(
            first_message,
            &Created,
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            Some(i64::MAX),
            "null".to_string(),
            false,
            true,
        );
    }

    #[test]
    fn deserialize_sqs_message() {
        test_deserialize_sqs_message(expected_sqs_record(false));
        test_deserialize_sqs_message(expected_sqs_record(true));
    }

    #[test]
    fn deserialize_event_bridge_message() {
        test_deserialize_event_bridge_message(&expected_event_bridge_record(false).to_string());
        test_deserialize_event_bridge_message(&expected_event_bridge_record(true).to_string());
    }

    #[test]
    fn deserialize_event_bridge_message_delete_marker() {
        let record = expected_event_bridge_record_delete_marker().to_string();

        let result: FlatS3EventMessages = serde_json::from_str(&record).unwrap();
        let first_message = result.into_inner().first().unwrap().clone();

        assert_flat_s3_event(
            first_message,
            &Deleted,
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            None,
            EXPECTED_VERSION_ID.to_string(),
            true,
            false,
        );
    }

    #[test]
    fn deserialize_sqs_message_delete_marker() {
        let mut record = expected_sqs_record(false);
        record["eventName"] = json!("ObjectRemoved:DeleteMarkerCreated");
        let message = json!({ "Records": [record] }).to_string();

        let result: FlatS3EventMessages = serde_json::from_str(&message).unwrap();
        let first_message = result.into_inner().first().unwrap().clone();

        assert_flat_s3_event(
            first_message,
            &Deleted,
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            None,
            EXPECTED_VERSION_ID.to_string(),
            true,
            false,
        );
    }

    fn test_deserialize_sqs_message(record: Value) {
        let message = json!({ "Records": [record] }).to_string();

        let result: FlatS3EventMessages = serde_json::from_str(&message).unwrap();
        let first_message = result.into_inner().first().unwrap().clone();

        assert_flat_s3_event(
            first_message,
            &Deleted,
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            None,
            EXPECTED_VERSION_ID.to_string(),
            false,
            false,
        );
    }

    fn test_deserialize_event_bridge_message(record: &str) {
        let result: FlatS3EventMessages = serde_json::from_str(record).unwrap();
        let first_message = result.into_inner().first().unwrap().clone();

        assert_flat_s3_event(
            first_message,
            &Deleted,
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            None,
            EXPECTED_VERSION_ID.to_string(),
            false,
            false,
        );
    }
}
