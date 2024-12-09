//! Routing logic for query filtering.
//!

use crate::database::entities::sea_orm_active_enums::{EventType, StorageClass};
use crate::routes::filter::wildcard::{Wildcard, WildcardEither};
use sea_orm::prelude::{DateTimeWithTimeZone, Json};
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use serde_json::Map;
use std::collections::HashMap;
use std::fmt::Display;
use std::result;
use std::str::FromStr;
use serde::de::Error;
use serde_with::{DisplayFromStr, serde_as, SerializeAs, DeserializeAs};
use serde_with::de::DeserializeAsWrap;
use serde_with::ser::SerializeAsWrap;
use utoipa::IntoParams;
use uuid::Uuid;

pub mod extract;
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
#[serde(default, rename_all = "camelCase", from = "FilterJoinUntagged<T>")]
pub struct FilterJoin<T>(pub HashMap<Join, Vec<T>>);

impl<T> Default for FilterJoin<T> {
    fn default() -> Self {
        Self(Default::default())
    }
}

/// The logical query join type.
#[derive(Serialize, Deserialize, Debug, Default, Clone, PartialEq, Eq, Hash)]
#[serde(rename_all = "camelCase")]
pub enum Join {
    #[default]
    And,
    Or,
}

impl<T> From<FilterJoinUntagged<T>> for FilterJoin<T> {
    fn from(join: FilterJoinUntagged<T>) -> Self {
        match join {
            FilterJoinUntagged::One(one) => one.into(),
            FilterJoinUntagged::Many(many) => many.into(),
            FilterJoinUntagged::Map(map) => Self(map),
        }
    }
}

impl<T> From<T> for FilterJoin<T> {
    fn from(one: T) -> Self {
        Self(HashMap::from_iter(vec![(Join::And, vec![one])]))
    }
}

impl<T> From<Vec<T>> for FilterJoin<T> {
    fn from(many: Vec<T>) -> Self {
        Self(HashMap::from_iter(vec![(Join::And, many)]))
    }
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq)]
#[serde(untagged, rename_all = "camelCase")]
enum FilterJoinUntagged<T> {
    One(T),
    Many(Vec<T>),
    Map(HashMap<Join, Vec<T>>),
}

fn filter_join_from_str<'de, D, T>(deserializer: D) -> Result<FilterJoin<T>, D::Error>
where D: Deserializer<'de>,
    T: FromStr,
    T::Err: Display {
    let value = FilterJoinUntagged::<String>::deserialize(deserializer)?;
    let map_from_str = |one: String| T::from_str(&one).map_err(Error::custom);
    let map_many_from_str = |many: Vec<String>| many.into_iter().map(map_from_str).collect::<Result<_, _>>();

    let from_str = match value {
        FilterJoinUntagged::One(one) => FilterJoinUntagged::One(map_from_str(one)?),
        FilterJoinUntagged::Many(many) => FilterJoinUntagged::Many(map_many_from_str(many)?),
        FilterJoinUntagged::Map(map) => {
            FilterJoinUntagged::Map(HashMap::from_iter(map.into_iter().map(|(join, many)| {
                Ok((join, map_many_from_str(many)?))
            }).collect::<Result<Vec<_>, _>>()?))
        },
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
    #[param(required = false)]
    pub(crate) event_type: Option<EventType>,
    /// Query by bucket. Supports wildcards.
    /// Repeated parameters are joined with an `and` conditions by default.
    #[param(required = false, value_type = Vec<Wildcard>)]
    pub(crate) bucket: FilterJoin<Wildcard>,
    /// Query by key. Supports wildcards.
    /// Repeated parameters are joined with an `and` conditions by default.
    #[param(required = false, value_type = Vec<Wildcard>)]
    pub(crate) key: FilterJoin<Wildcard>,
    /// Query by version_id. Supports wildcards.
    /// Repeated parameters are joined with an `and` conditions by default.
    #[param(required = false, value_type = Vec<Wildcard>)]
    pub(crate) version_id: FilterJoin<Wildcard>,
    /// Query by event_time. Supports wildcards.
    /// Repeated parameters are joined with an `and` conditions by default.
    #[param(required = false, value_type = Vec<Wildcard>)]
    pub(crate) event_time: FilterJoin<WildcardEither<DateTimeWithTimeZone>>,
    /// Query by size.
    /// Repeated parameters are joined with an `and` conditions by default.
    #[serde(deserialize_with = "filter_join_from_str")]
    #[param(required = false, value_type = Vec<i64>)]
    pub(crate) size: FilterJoin<i64>,
    /// Query by the sha256 checksum.
    /// Repeated parameters are joined with an `and` conditions by default.
    #[param(required = false, value_type = Vec<Wildcard>)]
    pub(crate) sha256: FilterJoin<String>,
    /// Query by the last modified date. Supports wildcards.
    /// Repeated parameters are joined with an `and` conditions by default.
    #[param(required = false, value_type = Vec<Wildcard>)]
    pub(crate) last_modified_date: FilterJoin<WildcardEither<DateTimeWithTimeZone>>,
    /// Query by the e_tag.
    /// Repeated parameters are joined with an `and` conditions by default.
    #[param(required = false, value_type = Vec<Wildcard>)]
    pub(crate) e_tag: FilterJoin<String>,
    /// Query by the storage class.
    /// Repeated parameters are joined with an `and` conditions by default.
    #[param(required = false, value_type = Vec<StorageClass>)]
    pub(crate) storage_class: FilterJoin<StorageClass>,
    /// Query by the object delete marker.
    #[param(required = false)]
    pub(crate) is_delete_marker: Option<bool>,
    /// Query by the ingest id that objects get tagged with.
    /// Repeated parameters are joined with an `and` conditions by default.
    #[param(required = false, value_type = Vec<Uuid>)]
    pub(crate) ingest_id: FilterJoin<Uuid>,
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
    use extract::tests::get_result;

    use super::*;

    #[test]
    fn deserialize_empty_params() {
        let params: S3ObjectsFilter = serde_qs::from_str("").unwrap();

        assert_eq!(params, Default::default());
    }

    #[tokio::test]
    async fn deserialize_single_params() {
        let qs = "/?\
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
        let params: S3ObjectsFilter = get_result(qs).await;

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
                storage_class: vec![StorageClass::DeepArchive].into(),
                is_delete_marker: Some(true),
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
        isDeleteMarker=true&\
        ingestId[]=00000000-0000-0000-0000-000000000000&ingestId[]=FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF&\
        attributes[attributeId]=id1\
        ";
        let params: S3ObjectsFilter = serde_qs::from_str(qs).unwrap();

        assert_many_params(params);
    }

    #[test]
    fn deserialize_many_params_and() {
        let qs = "\
        eventType=Created&\
        key[and]=key1&key[and]=key2&\
        bucket[and]=bucket1&bucket[and]=bucket2&\
        versionId[and]=version_id1&versionId[and]=version_id2&\
        eventTime[and]=1970-01-02T00:00:00Z&eventTime[and]=1970-01-02T00:00:01Z&\
        size[and]=4&size[and]=5&\
        sha256[and]=sha256&sha256[and]=sha1&\
        lastModifiedDate[and]=1970-01-02T00:00:00Z&lastModifiedDate[and]=1970-01-02T00:00:01Z&\
        eTag[and]=eTag1&eTag[and]=eTag2&\
        storageClass[and]=DeepArchive&storageClass[and]=Glacier&\
        isDeleteMarker=true&\
        ingestId[and]=00000000-0000-0000-0000-000000000000&ingestId[and]=FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF&\
        attributes[attributeId]=id1\
        ";
        let params: S3ObjectsFilter = serde_qs::from_str(qs).unwrap();

        assert_many_params(params);
    }

    fn assert_many_params(params: S3ObjectsFilter) {
        assert_eq!(
            params,
            S3ObjectsFilter {
                event_type: Some(EventType::Created),
                key: vec![
                    Wildcard::new("key1".to_string()),
                    Wildcard::new("key2".to_string())
                ]
                    .into(),
                bucket: vec![
                    Wildcard::new("bucket1".to_string()),
                    Wildcard::new("bucket2".to_string())
                ]
                    .into(),
                version_id: vec![
                    Wildcard::new("version_id1".to_string()),
                    Wildcard::new("version_id2".to_string())
                ]
                    .into(),
                event_time: vec![
                    WildcardEither::Or("1970-01-02T00:00:00Z".parse().unwrap()),
                    WildcardEither::Or("1970-01-02T00:00:01Z".parse().unwrap())
                ]
                    .into(),
                size: vec![4, 5].into(),
                sha256: vec!["sha256".to_string(), "sha1".to_string()].into(),
                last_modified_date: vec![
                    WildcardEither::Or("1970-01-02T00:00:00Z".parse().unwrap()),
                    WildcardEither::Or("1970-01-02T00:00:01Z".parse().unwrap())
                ]
                    .into(),
                e_tag: vec!["eTag1".to_string(), "eTag2".to_string()].into(),
                storage_class: vec![StorageClass::DeepArchive, StorageClass::Glacier].into(),
                is_delete_marker: Some(true),
                ingest_id: vec![Uuid::nil(), Uuid::max()].into(),
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
