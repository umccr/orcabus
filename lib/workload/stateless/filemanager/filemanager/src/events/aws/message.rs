use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::postgres::{PgHasArrayType, PgTypeInfo};

use crate::events::aws::{FlatS3EventMessage, FlatS3EventMessages};
use crate::uuid::UuidGenerator;

#[derive(Debug, Default, Eq, PartialEq, Ord, PartialOrd, Clone, Hash, sqlx::Type)]
#[sqlx(type_name = "event_type")]
pub enum EventType {
    #[default]
    Created,
    Deleted,
    Other,
}

impl PgHasArrayType for EventType {
    fn array_type_info() -> PgTypeInfo {
        PgTypeInfo::with_name("_event_type")
    }
}

impl From<&str> for EventType {
    fn from(value: &str) -> Self {
        if value.contains("Object Created") || value.contains("ObjectCreated") {
            Self::Created
        } else if value.contains("Object Deleted") || value.contains("ObjectRemoved") {
            Self::Deleted
        } else {
            Self::Other
        }
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
    pub size: Option<i32>,
    #[serde(alias = "eTag")]
    pub etag: Option<String>,
    #[serde(alias = "versionId")]
    pub version_id: Option<String>,
    pub sequencer: Option<String>,
}

impl From<Record> for FlatS3EventMessages {
    fn from(record: Record) -> Self {
        let Record {
            time,
            detail_type,
            detail,
        } = record;

        let S3Record { bucket, object } = detail;

        let Bucket { name: bucket } = bucket;

        let Object {
            key,
            size,
            etag,
            version_id,
            sequencer,
        } = object;

        FlatS3EventMessages(vec![FlatS3EventMessage {
            s3_object_id: UuidGenerator::generate(),
            event_time: Some(time),
            bucket,
            key,
            size,
            e_tag: etag,
            sequencer,
            version_id: version_id.unwrap_or_else(FlatS3EventMessage::default_version_id),
            // Head fields are fetched later.
            storage_class: None,
            last_modified_date: None,
            event_type: detail_type.as_str().into(),
            number_reordered: 0,
            number_duplicate_events: 0,
        }])
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

#[cfg(test)]
mod tests {
    use serde_json::json;

    use crate::events::aws::tests::{
        assert_flat_s3_event, expected_event_bridge_record, expected_sqs_record,
        EXPECTED_SEQUENCER_DELETED_ONE, EXPECTED_VERSION_ID,
    };
    use crate::events::aws::EventType::Deleted;
    use crate::events::aws::FlatS3EventMessages;

    #[test]
    fn deserialize_sqs_message() {
        let record = expected_sqs_record();
        let message = json!({
           "Records": [record]
        })
        .to_string();

        let result: FlatS3EventMessages = serde_json::from_str(&message).unwrap();
        let first_message = result.into_inner().first().unwrap().clone();

        assert_flat_s3_event(
            first_message,
            &Deleted,
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            None,
            EXPECTED_VERSION_ID.to_string(),
        );
    }

    #[test]
    fn deserialize_event_bridge_message() {
        let record = expected_event_bridge_record().to_string();

        let result: FlatS3EventMessages = serde_json::from_str(&record).unwrap();
        let first_message = result.into_inner().first().unwrap().clone();

        assert_flat_s3_event(
            first_message,
            &Deleted,
            Some(EXPECTED_SEQUENCER_DELETED_ONE.to_string()),
            None,
            EXPECTED_VERSION_ID.to_string(),
        );
    }
}
