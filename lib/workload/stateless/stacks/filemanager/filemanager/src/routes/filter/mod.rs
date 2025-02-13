//! Routing logic for query filtering.
//!

use crate::database::entities::sea_orm_active_enums::{
    ArchiveStatus, EventType, Reason, StorageClass,
};
use crate::routes::filter::wildcard::{Wildcard, WildcardEither};
use sea_orm::prelude::{DateTimeWithTimeZone, Json};
use serde::de::Error;
use serde::{Deserialize, Deserializer, Serialize};
use serde_json::Map;
use std::collections::HashMap;
use std::fmt::Display;
use std::str::FromStr;
use utoipa::{IntoParams, ToSchema};
use uuid::Uuid;

pub mod crawl;
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

/// Specifies how to join multiple queries with the same key. Either with
/// 'or' or 'and' logic.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq)]
#[serde(default, rename_all = "camelCase", from = "FilterJoin<T>")]
pub struct FilterJoinMerged<T>(pub HashMap<Join, Vec<T>>);

impl<T> Default for FilterJoinMerged<T> {
    fn default() -> Self {
        Self(Default::default())
    }
}

/// The logical query join type.
#[derive(Serialize, Deserialize, Debug, Default, Clone, Copy, ToSchema, PartialEq, Eq, Hash)]
#[serde(rename_all = "camelCase")]
pub enum Join {
    #[default]
    Or,
    And,
}

impl<T> From<FilterJoin<T>> for FilterJoinMerged<T> {
    fn from(join: FilterJoin<T>) -> Self {
        match join {
            FilterJoin::One(one) => one.into(),
            FilterJoin::Many(many) => many.into(),
            FilterJoin::Map(map) => Self(map),
        }
    }
}

impl<T> From<T> for FilterJoinMerged<T> {
    fn from(one: T) -> Self {
        Self(HashMap::from_iter(vec![(Join::Or, vec![one])]))
    }
}

impl<T> From<Vec<T>> for FilterJoinMerged<T> {
    fn from(many: Vec<T>) -> Self {
        Self(HashMap::from_iter(vec![(Join::Or, many)]))
    }
}

impl<T> From<HashMap<Join, Vec<T>>> for FilterJoinMerged<T> {
    fn from(map: HashMap<Join, Vec<T>>) -> Self {
        Self(map)
    }
}

/// Specifies how to join multiple queries with the same key. Either with
/// 'or' or 'and' logic. The default is combining using `or` logic for multiple
/// keys. For example, use `?key[]=123&key[]=456` to query where `key=123`
/// or `key=456`. The same query can be expressed more explicitly as
/// `?key[or][]=123&key[or][]=456`. `and` logic can be expressed using the `and`
/// keyword. For example, use`?key[and][]=*123*&key[and][]=*345` to query where
/// the key contains `123` and ends with `345`.
#[derive(Serialize, Deserialize, Debug, ToSchema, Clone, PartialEq, Eq)]
#[serde(untagged, rename_all = "camelCase")]
pub enum FilterJoin<T> {
    One(T),
    Many(Vec<T>),
    Map(HashMap<Join, Vec<T>>),
}

fn filter_join_from_str<'de, D, T>(deserializer: D) -> Result<FilterJoinMerged<T>, D::Error>
where
    D: Deserializer<'de>,
    T: FromStr,
    T::Err: Display,
{
    let value = FilterJoin::<String>::deserialize(deserializer)?;
    let map_from_str = |one: String| T::from_str(&one).map_err(Error::custom);
    let map_many_from_str =
        |many: Vec<String>| many.into_iter().map(map_from_str).collect::<Result<_, _>>();

    let from_str = match value {
        FilterJoin::One(one) => FilterJoin::One(map_from_str(one)?),
        FilterJoin::Many(many) => FilterJoin::Many(map_many_from_str(many)?),
        FilterJoin::Map(map) => FilterJoin::Map(HashMap::from_iter(
            map.into_iter()
                .map(|(join, many)| Ok((join, map_many_from_str(many)?)))
                .collect::<Result<Vec<_>, _>>()?,
        )),
    };

    Ok(from_str.into())
}

/// The available fields to filter `s3_object` queries by. Each query parameter represents
/// an `and` clause in the SQL statement. Nested query string style syntax is supported on
/// JSON attributes. Wildcards are supported on some of the fields.
#[derive(Serialize, Deserialize, Debug, Default, IntoParams, Clone, PartialEq, Eq)]
#[serde(default, rename_all = "camelCase")]
#[into_params(parameter_in = Query)]
pub struct S3ObjectsFilter {
    /// Query by event type.
    #[param(nullable = false, required = false)]
    pub(crate) event_type: Option<EventType>,
    /// Query by bucket. Supports wildcards.
    /// Repeated parameters with `[]` are joined with an `or` conditions by default.
    /// Use `[or][]` or `[and][]` to explicitly set the joining logic.
    #[param(nullable = false, required = false, value_type = FilterJoin<Wildcard>)]
    pub(crate) bucket: FilterJoinMerged<Wildcard>,
    /// Query by key. Supports wildcards.
    /// Repeated parameters with `[]` are joined with an `or` conditions by default.
    /// Use `[or][]` or `[and][]` to explicitly set the joining logic.
    #[param(nullable = false, required = false, value_type = FilterJoin<Wildcard>)]
    pub(crate) key: FilterJoinMerged<Wildcard>,
    /// Query by version_id. Supports wildcards.
    /// Repeated parameters with `[]` are joined with an `or` conditions by default.
    /// Use `[or][]` or `[and][]` to explicitly set the joining logic.
    #[param(nullable = false, required = false, value_type = FilterJoin<Wildcard>)]
    pub(crate) version_id: FilterJoinMerged<Wildcard>,
    /// Query by event_time. Supports wildcards.
    /// Repeated parameters with `[]` are joined with an `or` conditions by default.
    /// Use `[or][]` or `[and][]` to explicitly set the joining logic.
    #[param(nullable = false, required = false, value_type = FilterJoin<Wildcard>)]
    pub(crate) event_time: FilterJoinMerged<WildcardEither<DateTimeWithTimeZone>>,
    /// Query by size.
    /// Repeated parameters with `[]` are joined with an `or` conditions by default.
    /// Use `[or][]` or `[and][]` to explicitly set the joining logic.
    #[serde(deserialize_with = "filter_join_from_str")]
    #[param(nullable = false, required = false, value_type = FilterJoin<i64>)]
    pub(crate) size: FilterJoinMerged<i64>,
    /// Query by the sha256 checksum.
    /// Repeated parameters with `[]` are joined with an `or` conditions by default.
    /// Use `[or][]` or `[and][]` to explicitly set the joining logic.
    #[param(nullable = false, required = false, value_type = FilterJoin<Wildcard>)]
    pub(crate) sha256: FilterJoinMerged<String>,
    /// Query by the last modified date. Supports wildcards.
    /// Repeated parameters with `[]` are joined with an `or` conditions by default.
    /// Use `[or][]` or `[and][]` to explicitly set the joining logic.
    #[param(nullable = false, required = false, value_type = FilterJoin<Wildcard>)]
    pub(crate) last_modified_date: FilterJoinMerged<WildcardEither<DateTimeWithTimeZone>>,
    /// Query by the e_tag.
    /// Repeated parameters with `[]` are joined with an `or` conditions by default.
    /// Use `[or][]` or `[and][]` to explicitly set the joining logic.
    #[param(nullable = false, required = false, value_type = FilterJoin<Wildcard>)]
    pub(crate) e_tag: FilterJoinMerged<String>,
    /// Query by the storage class.
    /// Repeated parameters with `[]` are joined with an `or` conditions by default.
    /// Use `[or][]` or `[and][]` to explicitly set the joining logic.
    #[param(nullable = false, required = false, value_type = FilterJoin<StorageClass>)]
    pub(crate) storage_class: FilterJoinMerged<StorageClass>,
    /// Query by the object delete marker.
    #[param(nullable = false, required = false)]
    pub(crate) is_delete_marker: Option<bool>,
    /// Query by the reason, which adds detail for why an event was generated, such as whether it
    /// was caused by API calls or lifecycle events. repeated parameters with `[]` are joined with
    /// an `or` conditions by default. Use `[or][]` or `[and][]` to explicitly set the joining logic.
    #[param(nullable = false, required = false, value_type = FilterJoin<Reason>)]
    pub(crate) reason: FilterJoinMerged<Reason>,
    /// Query by the archive status. The archive status can be `DeepArchiveAccess` or `ArchiveAccess`
    /// if the storage class is also `IntelligentTiering`. Repeated parameters with `[]` are joined
    /// with an `or` conditions by default. Use `[or][]` or `[and][]` to explicitly set the joining
    /// logic.
    #[param(nullable = false, required = false, value_type = FilterJoin<ArchiveStatus>)]
    pub(crate) archive_status: FilterJoinMerged<ArchiveStatus>,
    /// Query by whether the storage class allows the object to be retrieved straight away rather
    /// than restored. Setting this to true will show records with storage classes that are not
    /// `Glacier` or `DeepArchive`, and don't have `ArchiveAccess` or `DeepArchiveAccess` set if
    /// they are intelligent tiering.
    #[param(nullable = false, required = false)]
    pub(crate) is_accessible: Option<bool>,
    /// Query by the ingest id that objects get tagged with.
    /// Repeated parameters with `[]` are joined with an `or` conditions by default.
    /// Use `[or][]` or `[and][]` to explicitly set the joining logic.
    #[param(nullable = false, required = false, value_type = FilterJoin<Uuid>)]
    pub(crate) ingest_id: FilterJoinMerged<Uuid>,
    /// Query by JSON attributes. Supports nested syntax to access inner
    /// fields, e.g. `attributes[attribute_id]=...`. This only deserializes
    /// into string fields, and does not support other JSON types. E.g.
    /// `attributes[attribute_id]=1` converts to `{ "attribute_id" = "1" }`
    /// rather than `{ "attribute_id" = 1 }`. Supports wildcards.
    #[param(nullable = false, required = false)]
    pub(crate) attributes: Option<Json>,
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::routes::filter::wildcard::Wildcard;
    use serde_json::json;

    #[test]
    fn deserialize_empty_params() {
        let params: S3ObjectsFilter = serde_qs::from_str("").unwrap();

        assert_eq!(params, Default::default());
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
        storageClass=IntelligentTiering&\
        isDeleteMarker=true&\
        reason=CreatedPut&\
        archiveStatus=DeepArchiveAccess&\
        isAccessible=true&\
        ingestId=00000000-0000-0000-0000-000000000000&\
        attributes[attributeId]=id\
        ";
        let params: S3ObjectsFilter = serde_qs::from_str(qs).unwrap();

        assert_eq!(
            params,
            S3ObjectsFilter {
                event_type: Some(EventType::Deleted),
                key: vec![Wildcard::new("key1".to_string())].into(),
                bucket: vec![Wildcard::new("bucket1".to_string())].into(),
                version_id: vec![Wildcard::new("version_id1".to_string())].into(),
                event_time: vec![WildcardEither::Or("1970-01-02T00:00:00Z".parse().unwrap())]
                    .into(),
                size: vec![4].into(),
                sha256: vec!["sha256".to_string()].into(),
                last_modified_date: vec![WildcardEither::Or(
                    "1970-01-02T00:00:00Z".parse().unwrap()
                )]
                .into(),
                e_tag: vec!["eTag".to_string()].into(),
                storage_class: vec![StorageClass::IntelligentTiering].into(),
                is_delete_marker: Some(true),
                reason: vec![Reason::CreatedPut].into(),
                archive_status: vec![ArchiveStatus::DeepArchiveAccess].into(),
                is_accessible: Some(true),
                ingest_id: vec![Uuid::nil()].into(),
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
        reason[]=CreatedPut&reason[]=CreatedPost&\
        isDeleteMarker=true&\
        isAccessible=false&\
        ingestId[]=00000000-0000-0000-0000-000000000000&ingestId[]=FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF&\
        attributes[attributeId]=id1\
        ";
        let params: S3ObjectsFilter = serde_qs::from_str(qs).unwrap();

        assert_many_params(params, Join::Or);
    }

    #[test]
    fn deserialize_many_params_and() {
        let qs = "\
        eventType=Created&\
        key[and][]=key1&key[and][]=key2&\
        bucket[and][]=bucket1&bucket[and][]=bucket2&\
        versionId[and][]=version_id1&versionId[and][]=version_id2&\
        eventTime[and][]=1970-01-02T00:00:00Z&eventTime[and][]=1970-01-02T00:00:01Z&\
        size[and][]=4&size[and][]=5&\
        sha256[and][]=sha256&sha256[and][]=sha1&\
        lastModifiedDate[and][]=1970-01-02T00:00:00Z&lastModifiedDate[and][]=1970-01-02T00:00:01Z&\
        eTag[and][]=eTag1&eTag[and][]=eTag2&\
        storageClass[and][]=DeepArchive&storageClass[and][]=Glacier&\
        reason[and][]=CreatedPut&reason[and][]=CreatedPost&\
        isDeleteMarker=true&\
        isAccessible=false&\
        ingestId[and][]=00000000-0000-0000-0000-000000000000&ingestId[and][]=FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF&\
        attributes[attributeId]=id1\
        ";
        let params: S3ObjectsFilter = serde_qs::from_str(qs).unwrap();

        assert_many_params(params, Join::And);
    }

    #[test]
    fn deserialize_many_params_or() {
        let qs = "\
        eventType=Created&\
        key[or][]=key1&key[or][]=key2&\
        bucket[or][]=bucket1&bucket[or][]=bucket2&\
        versionId[or][]=version_id1&versionId[or][]=version_id2&\
        eventTime[or][]=1970-01-02T00:00:00Z&eventTime[or][]=1970-01-02T00:00:01Z&\
        size[or][]=4&size[or][]=5&\
        sha256[or][]=sha256&sha256[or][]=sha1&\
        lastModifiedDate[or][]=1970-01-02T00:00:00Z&lastModifiedDate[or][]=1970-01-02T00:00:01Z&\
        eTag[or][]=eTag1&eTag[or][]=eTag2&\
        storageClass[or][]=DeepArchive&storageClass[or][]=Glacier&\
        reason[or][]=CreatedPut&reason[or][]=CreatedPost&\
        isDeleteMarker=true&\
        isAccessible=false&\
        ingestId[or][]=00000000-0000-0000-0000-000000000000&ingestId[or][]=FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF&\
        attributes[attributeId]=id1\
        ";
        let params: S3ObjectsFilter = serde_qs::from_str(qs).unwrap();

        assert_many_params(params, Join::Or);
    }

    fn assert_many_params(params: S3ObjectsFilter, join: Join) {
        let date: FilterJoinMerged<_> = HashMap::from_iter(vec![(
            join,
            vec![
                WildcardEither::Or("1970-01-02T00:00:00Z".parse().unwrap()),
                WildcardEither::Or("1970-01-02T00:00:01Z".parse().unwrap()),
            ],
        )])
        .into();

        assert_eq!(
            params,
            S3ObjectsFilter {
                event_type: Some(EventType::Created),
                key: HashMap::from_iter(vec![(
                    join,
                    vec![
                        Wildcard::new("key1".to_string()),
                        Wildcard::new("key2".to_string())
                    ]
                )])
                .into(),
                bucket: HashMap::from_iter(vec![(
                    join,
                    vec![
                        Wildcard::new("bucket1".to_string()),
                        Wildcard::new("bucket2".to_string())
                    ]
                )])
                .into(),
                version_id: HashMap::from_iter(vec![(
                    join,
                    vec![
                        Wildcard::new("version_id1".to_string()),
                        Wildcard::new("version_id2".to_string())
                    ]
                )])
                .into(),
                event_time: date.clone(),
                size: HashMap::from_iter(vec![(join, vec![4, 5])]).into(),
                sha256: HashMap::from_iter(vec![(
                    join,
                    vec!["sha256".to_string(), "sha1".to_string()]
                )])
                .into(),
                last_modified_date: date,
                e_tag: HashMap::from_iter(vec![(
                    join,
                    vec!["eTag1".to_string(), "eTag2".to_string()]
                )])
                .into(),
                storage_class: HashMap::from_iter(vec![(
                    join,
                    vec![StorageClass::DeepArchive, StorageClass::Glacier]
                )])
                .into(),
                reason: HashMap::from_iter(vec![(
                    join,
                    vec![Reason::CreatedPut, Reason::CreatedPost]
                )])
                .into(),
                archive_status: HashMap::from_iter(vec![]).into(),
                is_delete_marker: Some(true),
                is_accessible: Some(false),
                ingest_id: HashMap::from_iter(vec![(join, vec![Uuid::nil(), Uuid::max()])]).into(),
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
