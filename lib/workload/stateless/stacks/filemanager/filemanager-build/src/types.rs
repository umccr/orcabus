use chrono::{DateTime, Utc};
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use serde_with::skip_serializing_none;
use std::ops::Not;
use uuid::Uuid;

/// A filemanager object state change event.
#[skip_serializing_none]
#[derive(Deserialize, Serialize, JsonSchema, Default)]
#[serde(rename_all = "kebab-case", default)]
pub struct FileStateChange {
    /// The type of the event.
    pub(crate) detail_type: FileStateChangeType,
    /// The detail of the event.
    pub(crate) detail: Detail,
    /// The source of the event.
    pub(crate) source: String,
    /// The version of the event.
    pub(crate) version: Option<String>,
    /// The ID of the event.
    pub(crate) id: Option<Uuid>,
    /// The account ID of the event.
    pub(crate) account: Option<String>,
    /// The time the event was generated.
    pub(crate) time: Option<DateTime<Utc>>,
    /// The region the event was generated in.
    pub(crate) region: Option<String>,
    /// The resources of the event.
    pub(crate) resources: Option<Vec<String>>,
}

/// The type of S3 object state change event.
#[derive(Deserialize, Serialize, JsonSchema, Default)]
#[serde(rename = "FileStateChange")]
pub enum FileStateChangeType {
    #[default]
    FileStateChange,
}

/// The detail of an S3 object state change event.
#[skip_serializing_none]
#[derive(Deserialize, Serialize, JsonSchema, Default)]
#[serde(rename_all = "kebab-case", default)]
pub struct Detail {
    /// The key name prefix to apply this transition to. Applies to all objects by default.
    pub(crate) prefix: Option<String>,
    /// A set of transitions to apply. Performs no transition by default.
    pub(crate) transitions: Option<Vec<Transition>>,
    /// The number of days to wait before expiring the object. Performs no expiry by default.
    pub(crate) expiration: Option<u64>,
    /// Apply the transition to objects that are less than the specified size. Applies to objects
    /// of any size by default.
    #[schemars(range(min = 1))]
    pub(crate) object_size_less_than: Option<u64>,
    /// Apply the transition to objects that are greater than the specified size. Applies to objects
    /// of any size by default.
    pub(crate) object_size_greater_than: Option<u64>,
    /// Whether to keep the expiry rule when the object is moved. By default, the rule is removed
    /// when an object is moved.
    #[serde(skip_serializing_if = "Not::not")]
    pub(crate) keep_on_move: bool,
}

/// An S3 storage class transition.
#[derive(Deserialize, Serialize, JsonSchema)]
#[serde(rename_all = "kebab-case")]
pub struct Transition {
    /// The storage class to transition to.
    pub(crate) storage_class: StorageClass,
    /// The number of days to wait before transitioning the object.
    pub(crate) days: u64,
}

/// AWS storage types.
#[derive(Debug, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum StorageClass {
    StandardIa,
    IntelligentTiering,
    OnezoneIa,
    Glacier,
    GlacierIr,
    DeepArchive,
}
