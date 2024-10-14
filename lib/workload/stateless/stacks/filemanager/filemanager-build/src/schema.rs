//! Logic for AWS EventBridge schema for filemanager.
//!

use crate::error::ErrorKind::SchemaGeneration;
use crate::error::Result;
use chrono::{DateTime, Utc};
use schemars::{schema_for, JsonSchema};
use serde::{Deserialize, Serialize};
use serde_json::to_string_pretty;
use std::path::Path;
use tokio::fs;
use uuid::Uuid;

/// A filemanager object state change event.
#[derive(Deserialize, Serialize, JsonSchema)]
#[serde(rename_all = "kebab-case")]
pub struct FileStateChange {
    /// The type of the event.
    detail_type: FileStateChangeType,
    /// The detail of the event.
    detail: Detail,
    /// The source of the event.
    source: String,
    /// The version of the event.
    version: Option<String>,
    /// The ID of the event.
    id: Option<Uuid>,
    /// The account ID of the event.
    account: Option<String>,
    /// The time the event was generated.
    time: Option<DateTime<Utc>>,
    /// The region the event was generated in.
    region: Option<String>,
    /// The resources of the event.
    resources: Option<Vec<String>>,
}

/// The type of S3 object state change event.
#[derive(Deserialize, Serialize, JsonSchema)]
#[serde(rename = "FileStateChange")]
pub enum FileStateChangeType {
    FileStateChange,
}

/// The detail of an S3 object state change event.
#[derive(Deserialize, Serialize, JsonSchema)]
#[serde(rename_all = "kebab-case")]
pub struct Detail {
    /// The key name prefix to apply this transition to. Applies to all objects by default.
    prefix: Option<String>,
    /// A set of transitions to apply. Performs no transition by default.
    transitions: Option<Vec<Transition>>,
    /// The number of days to wait before expiring the object. Performs no expiry by default.
    expiration: Option<u64>,
    /// Apply the transition to objects that are less than the specified size. Applies to objects
    /// of any size by default.
    #[schemars(range(min = 1))]
    object_size_less_than: Option<u64>,
    /// Apply the transition to objects that are greater than the specified size. Applies to objects
    /// of any size by default.
    object_size_greater_than: Option<u64>,
    /// Whether to keep the expiry rule when the object is moved. By default, the rule is removed
    /// when an object is moved.
    keep_on_move: bool,
}

/// An S3 storage class transition.
#[derive(Deserialize, Serialize, JsonSchema)]
#[serde(rename_all = "kebab-case")]
pub struct Transition {
    /// The storage class to transition to.
    storage_class: StorageClass,
    /// The number of days to wait before transitioning the object.
    days: String,
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

/// Generate the JSON schemas.
pub async fn generate_schemas(out_file: &Path) -> Result<()> {
    let schema = to_string_pretty(&schema_for!(FileStateChange))
        .map_err(|err| SchemaGeneration(err.to_string()))?;

    fs::write(out_file, schema)
        .await
        .map_err(|err| SchemaGeneration(err.to_string()))?;

    Ok(())
}
