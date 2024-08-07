//! Routing logic for query filtering.
//!

pub mod wildcard;

use crate::database::entities::sea_orm_active_enums::{EventType, StorageClass};
use crate::routes::filter::wildcard::WildcardEither;
use sea_orm::prelude::{DateTimeWithTimeZone, Json};
use serde::{Deserialize, Serialize};
use utoipa::{IntoParams, ToSchema};

/// The available fields to filter `s3_object` queries by. Each query parameter represents
/// an `and` clause in the SQL statement. Nested query string style syntax is supported on
/// JSON attributes. Wildcards are supported on some of the fields.
#[derive(Serialize, Deserialize, Debug, Default, IntoParams, ToSchema)]
#[serde(default)]
#[into_params(parameter_in = Query)]
pub struct S3ObjectsFilter {
    #[param(required = false)]
    /// Query by event type.
    pub(crate) event_type: Option<WildcardEither<EventType>>,
    #[param(required = false)]
    /// Query by bucket.
    pub(crate) bucket: Option<WildcardEither<String>>,
    #[param(required = false)]
    /// Query by key.
    pub(crate) key: Option<WildcardEither<String>>,
    #[param(required = false)]
    /// Query by version_id.
    pub(crate) version_id: Option<WildcardEither<String>>,
    #[param(required = false)]
    /// Query by date. Supports wildcards.
    pub(crate) date: Option<WildcardEither<DateTimeWithTimeZone>>,
    #[param(required = false)]
    /// Query by size.
    pub(crate) size: Option<i64>,
    #[param(required = false)]
    /// Query by the sha256 checksum.
    pub(crate) sha256: Option<String>,
    #[param(required = false)]
    /// Query by the last modified date.
    pub(crate) last_modified_date: Option<WildcardEither<DateTimeWithTimeZone>>,
    #[param(required = false)]
    /// Query by the e_tag.
    pub(crate) e_tag: Option<String>,
    #[param(required = false)]
    /// Query by the storage class.
    pub(crate) storage_class: Option<WildcardEither<StorageClass>>,
    #[param(required = false)]
    /// Query by the object delete marker.
    pub(crate) is_delete_marker: Option<bool>,
    #[param(required = false)]
    /// Query by JSON attributes. Supports nested syntax to access inner
    /// fields, e.g. `attributes[attribute_id]=...`. This only deserializes
    /// into string fields, and does not support other JSON types. E.g.
    /// `attributes[attribute_id]=1` converts to `{ "attribute_id" = "1" }`
    /// rather than `{ "attribute_id" = 1 }`.
    pub(crate) attributes: Option<Json>,
}

/// The available fields to filter `object` queries by. Each query parameter represents
/// an `and` clause in the SQL statement. Nested query string style syntax is supported on
/// JSON attributes.
#[derive(Serialize, Deserialize, Debug, Default, IntoParams, ToSchema)]
#[serde(default)]
#[into_params(parameter_in = Query)]
pub struct ObjectsFilter {
    #[param(required = false)]
    /// Query by JSON attributes. Supports nested syntax to access inner
    /// fields, e.g. `attributes[attribute_id]=...`. This only deserializes
    /// into string fields, and does not support other JSON types. E.g.
    /// `attributes[attribute_id]=1` converts to `{ "attribute_id" = "1" }`
    /// rather than `{ "attribute_id" = 1 }`.
    pub(crate) attributes: Option<Json>,
}
