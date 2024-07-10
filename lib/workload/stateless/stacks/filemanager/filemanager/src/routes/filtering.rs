//! API filtering related query logic.
//!

use crate::database::entities::sea_orm_active_enums::{EventType, StorageClass};
use sea_orm::prelude::{DateTimeWithTimeZone, Json};
use serde::{Deserialize, Serialize};
use utoipa::{IntoParams, ToSchema};

/// The available fields to filter `s3_object` queries by. Each query parameter represents
/// an `and` clause in the SQL statement. Nested query string style syntax is supported on
/// JSON attributes.
#[derive(Serialize, Deserialize, Debug, Default, IntoParams, ToSchema)]
#[serde(default)]
pub struct S3ObjectsFilterByAll {
    #[param(nullable)]
    /// Query by event type.
    event_type: Option<EventType>,
    #[param(nullable)]
    /// Query by bucket.
    bucket: Option<String>,
    #[param(nullable)]
    /// Query by key.
    key: Option<String>,
    #[param(nullable)]
    /// Query by version_id.
    version_id: Option<String>,
    #[param(nullable)]
    /// Query by date.
    date: Option<DateTimeWithTimeZone>,
    #[param(nullable)]
    /// Query by size.
    size: Option<i64>,
    #[param(nullable)]
    /// Query by the sha256 checksum.
    sha256: Option<String>,
    #[param(nullable)]
    /// Query by the last modified date.
    last_modified_date: Option<DateTimeWithTimeZone>,
    #[param(nullable)]
    /// Query by the e_tag.
    e_tag: Option<String>,
    #[param(nullable)]
    /// Query by the storage class.
    storage_class: Option<StorageClass>,
    #[param(nullable)]
    /// Query by the object delete marker.
    is_delete_marker: bool,
    #[param(nullable)]
    /// Query by JSON attributes. Supports nested syntax to access inner
    /// fields, e.g. `?attributes[attribute_id]=...`
    attributes: Option<Json>
}

/// The available fields to filter `object` queries by. Each query parameter represents
/// an `and` clause in the SQL statement. Nested query string style syntax is supported on
/// JSON attributes.
#[derive(Serialize, Deserialize, Debug, Default, IntoParams, ToSchema)]
#[serde(default)]
pub struct ObjectsFilterByAll {
    #[param(nullable)]
    /// Query by JSON attributes. Supports nested syntax to access inner
    /// fields, e.g. `?attributes[attribute_id]=...`
    attributes: Option<Json>
}
