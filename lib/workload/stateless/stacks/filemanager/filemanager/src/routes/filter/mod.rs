//! Routing logic for query filtering.
//!

use crate::database::entities::sea_orm_active_enums::{EventType, StorageClass};
use crate::routes::filter::wildcard::{Wildcard, WildcardEither};
use sea_orm::prelude::{DateTimeWithTimeZone, Json};
use serde::{Deserialize, Serialize};
use serde_json::Map;
use serde_with::serde_as;
use serde_with::{DisplayFromStr, OneOrMany};
use utoipa::IntoParams;
use uuid::Uuid;

pub mod wildcard;

/// Capture any parameters and assume that they are top-level attributes fields.
#[derive(Serialize, Deserialize, Debug, Default, Eq, PartialEq, IntoParams)]
#[serde(default, transparent, rename_all = "camelCase")]
#[into_params(names("params"), parameter_in = Query)]
pub struct AttributesOnlyFilter(Map<String, Json>);

impl From<AttributesOnlyFilter> for S3ObjectsFilter {
    /// Convert to `S3ObjectsFilter`, merging into `attributes`.
    fn from(value: AttributesOnlyFilter) -> Self {
        Self {
            attributes: Some(Json::Object(value.0)),
            ..Default::default()
        }
    }
}

/// The available fields to filter `s3_object` queries by. Each query parameter represents
/// an `and` clause in the SQL statement. Nested query string style syntax is supported on
/// JSON attributes. Wildcards are supported on some of the fields.
#[serde_as]
#[derive(Serialize, Deserialize, Debug, Default, IntoParams, Clone, PartialEq, Eq)]
#[serde(default, rename_all = "camelCase")]
#[into_params(parameter_in = Query)]
pub struct S3ObjectsFilter {
    /// Query by event type.
    #[param(required = false)]
    pub(crate) event_type: Option<EventType>,
    /// Query by bucket. Supports wildcards.
    /// Repeated parameters are joined with an `or` condition.
    #[serde_as(as = "OneOrMany<_>")]
    #[param(required = false)]
    pub(crate) bucket: Vec<Wildcard>,
    /// Query by key. Supports wildcards.
    /// Repeated parameters are joined with an `or` condition.
    #[serde_as(as = "OneOrMany<_>")]
    #[param(required = false)]
    pub(crate) key: Vec<Wildcard>,
    /// Query by version_id. Supports wildcards.
    /// Repeated parameters are joined with an `or` condition.
    #[serde_as(as = "OneOrMany<_>")]
    #[param(required = false)]
    pub(crate) version_id: Vec<Wildcard>,
    /// Query by event_time. Supports wildcards.
    /// Repeated parameters are joined with an `or` condition.
    #[serde_as(as = "OneOrMany<_>")]
    #[param(required = false, value_type = Wildcard)]
    pub(crate) event_time: Vec<WildcardEither<DateTimeWithTimeZone>>,
    /// Query by size.
    /// Repeated parameters are joined with an `or` condition.
    #[serde_as(as = "OneOrMany<DisplayFromStr>")]
    #[param(required = false)]
    pub(crate) size: Vec<i64>,
    /// Query by the sha256 checksum.
    /// Repeated parameters are joined with an `or` condition.
    #[serde_as(as = "OneOrMany<_>")]
    #[param(required = false)]
    pub(crate) sha256: Vec<String>,
    /// Query by the last modified date. Supports wildcards.
    /// Repeated parameters are joined with an `or` condition.
    #[serde_as(as = "OneOrMany<_>")]
    #[param(required = false, value_type = Wildcard)]
    pub(crate) last_modified_date: Vec<WildcardEither<DateTimeWithTimeZone>>,
    /// Query by the e_tag.
    /// Repeated parameters are joined with an `or` condition.
    #[serde_as(as = "OneOrMany<_>")]
    #[param(required = false)]
    pub(crate) e_tag: Vec<String>,
    /// Query by the storage class.
    /// Repeated parameters are joined with an `or` condition.
    #[serde_as(as = "OneOrMany<_>")]
    #[param(required = false)]
    pub(crate) storage_class: Vec<StorageClass>,
    /// Query by the object delete marker.
    #[param(required = false)]
    pub(crate) is_delete_marker: Option<bool>,
    /// Query by the ingest id that objects get tagged with.
    /// Repeated parameters are joined with an `or` condition.
    #[serde_as(as = "OneOrMany<_>")]
    #[param(required = false)]
    pub(crate) ingest_id: Vec<Uuid>,
    /// Query by JSON attributes. Supports nested syntax to access inner
    /// fields, e.g. `attributes[attribute_id]=...`. This only deserializes
    /// into string fields, and does not support other JSON types. E.g.
    /// `attributes[attribute_id]=1` converts to `{ "attribute_id" = "1" }`
    /// rather than `{ "attribute_id" = 1 }`. Supports wildcards.
    #[param(required = false)]
    pub(crate) attributes: Option<Json>,
}

#[cfg(test)]
mod tests {
    use crate::routes::filter::wildcard::Wildcard;
    use serde_json::json;

    use super::*;

    #[test]
    fn deserialize_empty_params() {
        let params: S3ObjectsFilter = serde_qs::from_str("").unwrap();

        assert_eq!(params, Default::default(),);
    }

    #[test]
    fn deserialize_single_params() {
        let qs = "\
        eventType=Deleted&\
        key=key1&\
        bucket=bucket1&\
        versionId=version_id1&\
        eventTime=1970-01-02T00:00:00Z&\
        size=4&\
        sha256=sha256&\
        lastModifiedDate=1970-01-02T00:00:00Z&\
        eTag=eTag&\
        storageClass=DeepArchive&\
        isDeleteMarker=true&\
        ingestId=00000000-0000-0000-0000-000000000000&\
        attributes[attributeId]=id\
        ";
        let params: S3ObjectsFilter = serde_qs::from_str(qs).unwrap();

        assert_eq!(
            params,
            S3ObjectsFilter {
                event_type: Some(EventType::Deleted),
                key: vec![Wildcard::new("key1".to_string())],
                bucket: vec![Wildcard::new("bucket1".to_string())],
                version_id: vec![Wildcard::new("version_id1".to_string())],
                event_time: vec![WildcardEither::Or("1970-01-02T00:00:00Z".parse().unwrap())],
                size: vec![4],
                sha256: vec!["sha256".to_string()],
                last_modified_date: vec![WildcardEither::Or(
                    "1970-01-02T00:00:00Z".parse().unwrap()
                )],
                e_tag: vec!["eTag".to_string()],
                storage_class: vec![StorageClass::DeepArchive],
                is_delete_marker: Some(true),
                ingest_id: vec![Uuid::nil()],
                attributes: Some(json!({"attributeId": "id"}))
            }
        );
    }

    #[test]
    fn deserialize_many_params() {
        let qs = "\
        eventType=Created&\
        key[]=key1&key[]=key2&\
        bucket[]=bucket1&bucket[]=bucket2&\
        versionId[]=version_id1&versionId[]=version_id2&\
        eventTime[]=1970-01-02T00:00:00Z&eventTime[]=1970-01-02T00:00:01Z&\
        size[]=4&size[]=5&\
        sha256[]=sha256&sha256[]=sha1&\
        lastModifiedDate[]=1970-01-02T00:00:00Z&lastModifiedDate[]=1970-01-02T00:00:01Z&\
        eTag[]=eTag1&eTag[]=eTag2&\
        storageClass[]=DeepArchive&storageClass[]=Glacier&\
        isDeleteMarker=true&\
        ingestId[]=00000000-0000-0000-0000-000000000000&ingestId[]=FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF&\
        attributes[attributeId]=id1\
        ";
        let params: S3ObjectsFilter = serde_qs::from_str(qs).unwrap();

        assert_eq!(
            params,
            S3ObjectsFilter {
                event_type: Some(EventType::Created),
                key: vec![
                    Wildcard::new("key1".to_string()),
                    Wildcard::new("key2".to_string())
                ],
                bucket: vec![
                    Wildcard::new("bucket1".to_string()),
                    Wildcard::new("bucket2".to_string())
                ],
                version_id: vec![
                    Wildcard::new("version_id1".to_string()),
                    Wildcard::new("version_id2".to_string())
                ],
                event_time: vec![
                    WildcardEither::Or("1970-01-02T00:00:00Z".parse().unwrap()),
                    WildcardEither::Or("1970-01-02T00:00:01Z".parse().unwrap())
                ],
                size: vec![4, 5],
                sha256: vec!["sha256".to_string(), "sha1".to_string()],
                last_modified_date: vec![
                    WildcardEither::Or("1970-01-02T00:00:00Z".parse().unwrap()),
                    WildcardEither::Or("1970-01-02T00:00:01Z".parse().unwrap())
                ],
                e_tag: vec!["eTag1".to_string(), "eTag2".to_string()],
                storage_class: vec![StorageClass::DeepArchive, StorageClass::Glacier],
                is_delete_marker: Some(true),
                ingest_id: vec![Uuid::nil(), Uuid::max()],
                attributes: Some(json!({"attributeId": "id1"}))
            }
        );
    }

    #[test]
    fn deserialize_attribute_only_filter() {
        let qs = "key=key&bucket=bucket&attributeId=attributeId&nestedId[attributeId]=wildcard*";
        let params: AttributesOnlyFilter = serde_qs::from_str(qs).unwrap();
        assert_eq!(
            S3ObjectsFilter::from(params),
            S3ObjectsFilter {
                attributes: Some(json!({
                    "key": "key",
                    "bucket": "bucket",
                    "attributeId": "attributeId",
                    "nestedId": {
                        "attributeId": "wildcard*"
                    }
                })),
                ..Default::default()
            }
        );
    }
}
