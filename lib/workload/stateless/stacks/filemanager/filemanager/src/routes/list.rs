//! Route logic for list API calls.
//!

use axum::extract::{Request, State};
use axum::http::header::{CONTENT_ENCODING, CONTENT_TYPE};
use axum::routing::get;
use axum::{extract, Json, Router};
use axum_extra::extract::WithRejection;
use itertools::Itertools;
use sea_orm::{ConnectionTrait, TransactionTrait};
use serde::{Deserialize, Serialize};
use serde_json::to_value;
use std::collections::HashSet;
use std::marker::PhantomData;
use url::Url;
use utoipa::{IntoParams, ToSchema};

use crate::database::entities::s3_object;
use crate::database::entities::s3_object::Model as S3;
use crate::error::Result;
use crate::queries::list::ListQueryBuilder;
use crate::routes::error::{ErrorStatusCode, QsQuery, Query};
use crate::routes::filter::{AttributesOnlyFilter, S3ObjectsFilter};
use crate::routes::header::HeaderParser;
use crate::routes::pagination::{ListResponse, Pagination};
use crate::routes::presign::{PresignedParams, PresignedUrlBuilder};
use crate::routes::AppState;

/// The return value for count operations showing the number of records in the database.
#[derive(Debug, Deserialize, Serialize, ToSchema, Eq, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ListCount {
    /// The number of records.
    n_records: u64,
}

impl ListCount {
    /// Create a new list count.
    pub fn new(n_records: u64) -> Self {
        ListCount { n_records }
    }

    /// Get the number of records.
    pub fn n_records(&self) -> u64 {
        self.n_records
    }
}

/// Params for wildcard requests.
#[derive(Debug, Serialize, Deserialize, Default, IntoParams)]
#[serde(default, rename_all = "camelCase")]
#[into_params(parameter_in = Query)]
pub struct WildcardParams {
    /// The case sensitivity when using filter operations with a wildcard.
    /// Setting this true means that an SQL `like` statement is used, and false
    /// means `ilike` is used.
    #[serde(default = "default_case_sensitivity")]
    #[param(nullable = false, required = false, default = true)]
    pub(crate) case_sensitive: bool,
}

impl WildcardParams {
    /// Create new wildcard params.
    pub fn new(case_sensitive: bool) -> Self {
        Self { case_sensitive }
    }

    /// Get the case sensitivity.
    pub fn case_sensitive(&self) -> bool {
        self.case_sensitive
    }
}

/// The default case sensitivity for s3 object filter queries.
pub fn default_case_sensitivity() -> bool {
    true
}

/// The default current state flag for s3 object filter queries.
pub fn default_current_state() -> bool {
    true
}

/// Params for a list s3 objects request.
#[derive(Debug, Serialize, Deserialize, Default, IntoParams)]
#[serde(default, rename_all = "camelCase")]
#[into_params(parameter_in = Query)]
pub struct ListS3Params {
    /// Fetch the current state of objects in storage.
    /// This ensures that only `Created` events which represent current
    /// objects in storage are returned, and any historical `Deleted`
    /// or `Created`events are omitted.
    ///
    /// For example, consider that there are three events for a given bucket, key and version_id
    /// in the following order: `Created` -> `Deleted` -> `Created`. Then setting
    /// `?current_state=true` would return only the last `Created` event.
    #[serde(default = "default_case_sensitivity")]
    #[param(nullable = false, required = false, default = true)]
    current_state: bool,
}

impl ListS3Params {
    /// Create the current state struct.
    pub fn new(current_state: bool) -> Self {
        Self { current_state }
    }

    /// Get the current state.
    pub fn current_state(&self) -> bool {
        self.current_state
    }
}

/// List all s3_objects according to the parameters.
#[utoipa::path(
    get,
    path = "/s3",
    responses(
        (status = OK, description = "The collection of s3_objects", body = ListResponse<S3>),
        ErrorStatusCode,
    ),
    params(Pagination, WildcardParams, ListS3Params, S3ObjectsFilter),
    context_path = "/api/v1",
    tag = "list",
)]
pub async fn list_s3(
    state: State<AppState>,
    WithRejection(extract::Query(pagination), _): Query<Pagination>,
    WithRejection(extract::Query(wildcard), _): Query<WildcardParams>,
    WithRejection(extract::Query(list), _): Query<ListS3Params>,
    WithRejection(serde_qs::axum::QsQuery(filter_all), _): QsQuery<S3ObjectsFilter>,
    request: Request,
) -> Result<Json<ListResponse<S3>>> {
    let txn = state.database_client().connection_ref().begin().await?;

    let response = ListQueryBuilder::<_, s3_object::Entity>::new(&txn).filter_all(
        filter_all.clone(),
        wildcard.case_sensitive(),
        list.current_state,
    )?;

    let url = if let Some(url) = state.config().api_links_url() {
        url
    } else {
        &HeaderParser::parse_host_url(&request, state.use_tls_links())?
    };

    let url = url.join(&HeaderParser::get_uri_path(&request))?;

    let Json(count) = count_s3_with_connection(
        &txn,
        WithRejection(extract::Query(wildcard), PhantomData),
        WithRejection(extract::Query(list), PhantomData),
        WithRejection(serde_qs::axum::QsQuery(filter_all), PhantomData),
    )
    .await?;
    let response = response
        .paginate_to_list_response(pagination, url, count.n_records)
        .await?;

    txn.commit().await?;

    Ok(Json(response))
}

/// Count all s3_objects according to the parameters.
#[utoipa::path(
    get,
    path = "/s3/count",
    responses(
        (status = OK, description = "The count of s3 objects", body = ListCount),
        ErrorStatusCode,
    ),
    params(WildcardParams, ListS3Params, S3ObjectsFilter),
    context_path = "/api/v1",
    tag = "list",
)]
pub async fn count_s3(
    state: State<AppState>,
    wildcard: Query<WildcardParams>,
    list: Query<ListS3Params>,
    filter_all: QsQuery<S3ObjectsFilter>,
) -> Result<Json<ListCount>> {
    count_s3_with_connection(
        state.database_client().connection_ref(),
        wildcard,
        list,
        filter_all,
    )
    .await
}

async fn count_s3_with_connection<C: ConnectionTrait>(
    connection: &C,
    WithRejection(extract::Query(wildcard), _): Query<WildcardParams>,
    WithRejection(extract::Query(list), _): Query<ListS3Params>,
    WithRejection(serde_qs::axum::QsQuery(filter_all), _): QsQuery<S3ObjectsFilter>,
) -> Result<Json<ListCount>> {
    let response = ListQueryBuilder::<_, s3_object::Entity>::new(connection).filter_all(
        filter_all,
        wildcard.case_sensitive(),
        list.current_state,
    )?;

    Ok(Json(response.to_list_count().await?))
}

/// Implementation of the presign URL route.
async fn presign_url(
    state: State<AppState>,
    pagination: Query<Pagination>,
    wildcard: Query<WildcardParams>,
    WithRejection(extract::Query(presigned), _): Query<PresignedParams>,
    WithRejection(serde_qs::axum::QsQuery(mut filter_all), _): QsQuery<S3ObjectsFilter>,
    request: Request,
    access_key_secret_id: Option<String>,
) -> Result<Json<ListResponse<Url>>> {
    let content_type = HeaderParser::new(request.headers()).parse_header(CONTENT_TYPE)?;
    let content_encoding = HeaderParser::new(request.headers()).parse_header(CONTENT_ENCODING)?;

    filter_all.is_accessible = Some(true);
    let Json(ListResponse {
        links,
        pagination,
        results,
    }) = list_s3(
        state.clone(),
        pagination,
        wildcard,
        WithRejection(extract::Query(ListS3Params::new(true)), PhantomData),
        WithRejection(serde_qs::axum::QsQuery(filter_all), PhantomData),
        request,
    )
    .await?;

    let mut urls = Vec::with_capacity(results.len());

    for result in results {
        if let Some(presigned) = PresignedUrlBuilder::presign_from_model(
            &state,
            result,
            presigned.response_content_disposition(),
            content_type.clone(),
            content_encoding.clone(),
            access_key_secret_id.as_deref(),
        )
        .await?
        {
            urls.push(presigned);
        }
    }

    Ok(Json(ListResponse::new(links, pagination, urls)))
}

/// Generate AWS presigned URLs for s3_objects according to the parameters.
/// This route implies `currentState=true` because only existing objects can be presigned. It will
/// only also return objects that are not in archive storage by setting `isAccessible=true`.
/// Fewer presigned URLs may be returned than the amount of objects in the database because some
/// objects may be over the `FILEMANAGER_API_PRESIGN_LIMIT`. Presigned URLs live for up to 7 days.
#[utoipa::path(
    get,
    path = "/s3/presign",
    responses(
        (status = OK, description = "The list of presigned urls", body = ListResponse<Url>),
        ErrorStatusCode,
    ),
    params(Pagination, WildcardParams, PresignedParams, S3ObjectsFilter),
    context_path = "/api/v1",
    tag = "list",
)]
pub async fn presign_s3(
    state: State<AppState>,
    pagination: Query<Pagination>,
    wildcard: Query<WildcardParams>,
    presigned: Query<PresignedParams>,
    filter_all: QsQuery<S3ObjectsFilter>,
    request: Request,
) -> Result<Json<ListResponse<Url>>> {
    let access_key_secret_id = state
        .config()
        .access_key_secret_id()
        .map(|secret| secret.to_string());
    // Always presign with the secret access key if it's available.
    presign_url(
        state,
        pagination,
        wildcard,
        presigned,
        filter_all,
        request,
        access_key_secret_id,
    )
    .await
}

/// List all S3 objects according to a set of attribute filter parameters.
/// This route is a convenience for querying using top-level attributes and accepts arbitrary
/// parameters. For example, instead of using `/api/v1/s3?attributes[attributeId]=...`, this route
/// can express the same query as `/api/v1/s3/attributes?attributeId=...`. Similar to the
/// `attributes` filter parameter, nested JSON queries are supported using the bracket notation.
/// Note that regular filtering parameters, like `key` or `bucket` are not supported on this route.
#[utoipa::path(
    get,
    path = "/s3/attributes",
    responses(
        (status = OK, description = "The collection of s3_objects", body = ListResponse<S3>),
        ErrorStatusCode,
    ),
    params(Pagination, WildcardParams, ListS3Params, AttributesOnlyFilter),
    context_path = "/api/v1",
    tag = "list",
)]
pub async fn attributes_s3(
    state: State<AppState>,
    pagination: Query<Pagination>,
    wildcard: Query<WildcardParams>,
    list: Query<ListS3Params>,
    WithRejection(serde_qs::axum::QsQuery(attributes_only), _): QsQuery<AttributesOnlyFilter>,
    request: Request,
) -> Result<Json<ListResponse<S3>>> {
    let mut filter = S3ObjectsFilter::from(attributes_only);

    // Remove keys with special meaning.
    filter.attributes.iter_mut().for_each(|attributes| {
        attributes
            .as_object_mut()
            .iter_mut()
            .for_each(|attributes| {
                state.params_field_names.iter().for_each(|key| {
                    attributes.remove(key);
                });
            })
    });

    list_s3(
        state,
        pagination,
        wildcard,
        list,
        WithRejection(serde_qs::axum::QsQuery(filter), PhantomData),
        request,
    )
    .await
}

fn params_keys<T: Serialize>(value: T) -> HashSet<String> {
    to_value(value)
        .expect("failed to serialize params")
        .as_object()
        .expect("params is not an object")
        .keys()
        .cloned()
        .collect()
}

/// Return the field names that have a special meaning for the attributes route.
pub fn attributes_s3_field_names() -> HashSet<String> {
    let pagination = params_keys(Pagination::default());
    let wildcard = params_keys(WildcardParams::default());
    let list = params_keys(ListS3Params::default());

    pagination.into_iter().merge(wildcard).merge(list).collect()
}

/// The router for list objects.
pub fn list_router() -> Router<AppState> {
    Router::new()
        .route("/s3", get(list_s3))
        .route("/s3/count", get(count_s3))
        .route("/s3/presign", get(presign_s3))
        .route("/s3/attributes", get(attributes_s3))
}

#[cfg(test)]
pub(crate) mod tests {
    use aws_sdk_s3::operation::get_object::GetObjectOutput;
    use aws_sdk_s3::primitives::ByteStream;
    use aws_smithy_mocks_experimental::{mock, mock_client, Rule, RuleMode};
    use axum::body::to_bytes;
    use axum::body::Body;
    use axum::http::header::{CONTENT_TYPE, HOST};
    use axum::http::{Method, Request, StatusCode};
    use percent_encoding::{percent_encode, NON_ALPHANUMERIC};
    use serde::de::DeserializeOwned;
    use serde_json::{from_slice, json};
    use sqlx::PgPool;
    use std::collections::HashMap;
    use tower::util::ServiceExt;
    use uuid::Uuid;

    use crate::clients::aws::s3;
    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::entities::sea_orm_active_enums::EventType;
    use crate::env::Config;
    use crate::queries::list::tests::filter_event_type;
    use crate::queries::update::tests::{assert_contains, entries_many};
    use crate::queries::update::tests::{change_key, change_many};
    use crate::queries::EntriesBuilder;
    use crate::routes::api_router;
    use crate::routes::pagination::Links;
    use crate::routes::presign::tests::assert_presigned_params;

    use super::*;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_api(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap()
            .s3_objects;

        let result: ListResponse<S3> = response_from_get(state, "/s3?currentState=false").await;
        assert_eq!(result.links(), &Links::new(None, None));
        assert_eq!(result.results(), entries);
        assert_eq!(result.pagination().count, 10);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_current_s3_paginate(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let entries = EntriesBuilder::default()
            .with_bucket_divisor(4)
            .with_key_divisor(3)
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap()
            .s3_objects;

        let result: ListResponse<S3> = response_from_get(state, "/s3?rowsPerPage=1&page=1").await;
        assert_eq!(
            result.links(),
            &Links::new(
                None,
                Some(
                    "http://example.com/s3?rowsPerPage=1&page=2"
                        .parse()
                        .unwrap()
                )
            )
        );
        assert_eq!(result.results(), vec![entries[2].clone()]);
        assert_eq!(result.pagination().count, 2);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_current_s3_paginate_https_links(pool: PgPool) {
        let state = AppState::from_pool(pool)
            .await
            .unwrap()
            .with_use_tls_links(true);
        let entries = EntriesBuilder::default()
            .with_bucket_divisor(4)
            .with_key_divisor(3)
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap()
            .s3_objects;

        let result: ListResponse<S3> = response_from_get(state, "/s3?rowsPerPage=1&page=1").await;
        assert_eq!(
            result.links(),
            &Links::new(
                None,
                Some(
                    "https://example.com/s3?rowsPerPage=1&page=2"
                        .parse()
                        .unwrap()
                )
            )
        );
        assert_eq!(result.results(), vec![entries[2].clone()]);
        assert_eq!(result.pagination().count, 2);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_current_s3_paginate_alternate_link(pool: PgPool) {
        let state = AppState::from_pool(pool)
            .await
            .unwrap()
            .with_config(Config {
                api_links_url: Some("https://localhost:8000".parse().unwrap()),
                ..Default::default()
            });
        let entries = EntriesBuilder::default()
            .with_bucket_divisor(4)
            .with_key_divisor(3)
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap()
            .s3_objects;

        let result: ListResponse<S3> = response_from_get(state, "/s3?rowsPerPage=1&page=1").await;
        assert_eq!(
            result.links(),
            &Links::new(
                None,
                Some(
                    "https://localhost:8000/s3?rowsPerPage=1&page=2"
                        .parse()
                        .unwrap()
                )
            )
        );
        assert_eq!(result.results(), vec![entries[2].clone()]);
        assert_eq!(result.pagination().count, 2);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_api_presign(pool: PgPool) {
        let client = mock_client!(
            aws_sdk_s3,
            RuleMode::Sequential,
            &[
                &mock_get_object("0", "0", b""),
                &mock_get_object("2", "2", b"")
            ]
        );

        let state = AppState::from_pool(pool)
            .await
            .unwrap()
            .with_s3_client(s3::Client::new(client));

        EntriesBuilder::default()
            .with_bucket_divisor(4)
            .with_key_divisor(3)
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap();

        let result: ListResponse<Url> = response_from_get(state, "/s3/presign").await;
        assert_eq!(result.links(), &Links::new(None, None,));
        assert_eq!(2, result.pagination().count);

        let query = result.results()[0].query().unwrap();
        assert!(query.contains("X-Amz-Expires=604800"));
        assert_presigned_params(query, "inline");

        assert_eq!(result.results()[0].path(), "/0/0");

        let query = result.results()[1].query().unwrap();
        assert_presigned_params(query, "inline");
        assert_eq!(result.results()[1].path(), "/2/2");
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_api_presign_not_accessible(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();

        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap();
        println!("{:#?}", entries);

        let result: ListResponse<Url> =
            response_from_get(state, "/s3/presign?key=0&bucket=0").await;
        assert_eq!(result.links(), &Links::new(None, None,));
        assert_eq!(0, result.pagination().count);
        assert_eq!(0, result.results().len());
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_api_presign_attachment(pool: PgPool) {
        let client = mock_client!(
            aws_sdk_s3,
            RuleMode::Sequential,
            &[
                &mock_get_object("0", "0", b""),
                &mock_get_object("2", "2", b"")
            ]
        );

        let state = AppState::from_pool(pool)
            .await
            .unwrap()
            .with_s3_client(s3::Client::new(client));

        EntriesBuilder::default()
            .with_bucket_divisor(4)
            .with_key_divisor(3)
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap();

        let result: ListResponse<Url> =
            response_from_get(state, "/s3/presign?responseContentDisposition=attachment").await;
        assert_eq!(result.links(), &Links::new(None, None,));
        assert_eq!(2, result.pagination().count);

        let query = result.results()[0].query().unwrap();
        assert!(query.contains("X-Amz-Expires=604800"));
        assert_presigned_params(query, "attachment%3B%20filename%3D%220%22");
        assert_eq!(result.results()[0].path(), "/0/0");

        let query = result.results()[1].query().unwrap();
        assert_presigned_params(query, "attachment%3B%20filename%3D%222%22");
        assert_eq!(result.results()[1].path(), "/2/2");
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_api_presign_different_count(pool: PgPool) {
        let client = mock_client!(
            aws_sdk_s3,
            RuleMode::Sequential,
            &[&mock_get_object("0", "0", b""),]
        );

        let config = Config {
            api_presign_limit: Some(2),
            ..Default::default()
        };
        let state = AppState::from_pool(pool)
            .await
            .unwrap()
            .with_config(config)
            .with_s3_client(s3::Client::new(client));

        EntriesBuilder::default()
            .with_bucket_divisor(4)
            .with_key_divisor(3)
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap();

        let result: ListResponse<Url> = response_from_get(state, "/s3/presign").await;
        assert_eq!(result.links(), &Links::new(None, None));
        assert_eq!(2, result.pagination().count);

        let query = result.results()[0].query().unwrap();
        assert!(query.contains("X-Amz-Expires=604800"));
        assert!(query.contains("response-content-disposition=inline"));
        assert_eq!(result.results()[0].path(), "/0/0");
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_current_s3_filter(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let entries = EntriesBuilder::default()
            .with_n(30)
            .with_bucket_divisor(8)
            .with_key_divisor(5)
            .build(state.database_client())
            .await
            .unwrap()
            .s3_objects;

        let result: ListResponse<S3> =
            response_from_get(state, "/s3?size=4&rowsPerPage=1&page=1").await;
        assert_eq!(result.links(), &Links::new(None, None));
        assert_eq!(result.results(), vec![entries[24].clone()]);
        assert_eq!(result.pagination().count, 1);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_filter_event_type(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap()
            .s3_objects;

        let result: ListResponse<S3> =
            response_from_get(state, "/s3?eventType=Deleted&currentState=false").await;
        assert_eq!(result.results().len(), 5);
        assert_eq!(
            result.results(),
            filter_event_type(entries, EventType::Deleted)
        );
        assert_eq!(result.pagination().count, 5);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_multiple_and_filters(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap()
            .s3_objects;

        let result: ListResponse<S3> =
            response_from_get(state, "/s3?currentState=false&bucket=1&key=2").await;
        assert_eq!(result.results(), vec![entries[2].clone()]);
        assert_eq!(result.pagination().count, 1);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_multiple_or_filters(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap()
            .s3_objects;

        let result: ListResponse<S3> =
            response_from_get(state, "/s3?currentState=false&key[]=3&key[]=4").await;
        assert_eq!(
            result.results(),
            vec![entries[3].clone(), entries[4].clone()]
        );
        assert_eq!(result.pagination().count, 2);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_multiple_filters_percent_encoded(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap()
            .s3_objects;

        let brackets = percent_encode("[]".as_ref(), NON_ALPHANUMERIC).to_string();
        let result: ListResponse<S3> = response_from_get(
            state,
            &format!("/s3?currentState=false&key{}=3&key{}=4", brackets, brackets),
        )
        .await;
        assert_eq!(
            result.results(),
            vec![entries[3].clone(), entries[4].clone()]
        );
        assert_eq!(result.pagination().count, 2);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_multiple_filters_same_key(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .with_keys(HashMap::from_iter(vec![
                (0, "overlap".to_string()),
                (1, "overlap".to_string()),
                (2, "overlap".to_string()),
                (3, "overlap".to_string()),
                (4, "overlap".to_string()),
                (5, "overlap".to_string()),
            ]))
            .with_prefixes(HashMap::from_iter(vec![
                (0, "prefix".to_string()),
                (1, "prefix".to_string()),
                (2, "prefix".to_string()),
                (3, "prefix".to_string()),
            ]))
            .with_suffixes(HashMap::from_iter(vec![
                (0, "suffix".to_string()),
                (1, "suffix".to_string()),
                (4, "suffix".to_string()),
                (5, "suffix".to_string()),
            ]))
            .build(state.database_client())
            .await
            .unwrap()
            .s3_objects;

        let result: ListResponse<S3> = response_from_get(
            state,
            "/s3?currentState=false&key[and][]=prefixover*&key[and][]=*rlapsuffix",
        )
        .await;
        let mut expected_first = entries[0].clone();
        expected_first.is_current_state = false;
        let mut expected_second = entries[1].clone();
        expected_second.is_current_state = false;
        assert_eq!(result.results(), vec![expected_first, expected_second]);
        assert_eq!(result.pagination().count, 2);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_filter_wildcard(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let mut entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap();

        let value = "test-!)regex_%like";
        change_key(state.database_client(), &entries, 0, value.to_string()).await;
        change_key(state.database_client(), &entries, 1, value.to_string()).await;
        entries.s3_objects[0].key = value.to_string();
        entries.s3_objects[1].key = value.to_string();

        let s3_objects: ListResponse<S3> =
            response_from_get(state.clone(), "/s3?key=te*&currentState=false").await;
        assert_contains(s3_objects.results(), &entries, 0..2);
        assert_eq!(s3_objects.pagination().count, 2);

        let query = percent_encode("tes?-!)regex_%like".as_bytes(), NON_ALPHANUMERIC).to_string();
        let s3_objects: ListResponse<S3> = response_from_get(
            state.clone(),
            &format!("/s3?key={query}&currentState=false"),
        )
        .await;
        assert_contains(s3_objects.results(), &entries, 0..2);
        assert_eq!(s3_objects.pagination().count, 2);

        let query = percent_encode("test???regex??like".as_bytes(), NON_ALPHANUMERIC).to_string();
        let s3_objects: ListResponse<S3> = response_from_get(
            state.clone(),
            &format!("/s3?key={query}&currentState=false"),
        )
        .await;
        assert_contains(s3_objects.results(), &entries, 0..2);
        assert_eq!(s3_objects.pagination().count, 2);

        let query = percent_encode("test-!)regex_%like".as_bytes(), NON_ALPHANUMERIC).to_string();
        let s3_objects: ListResponse<S3> = response_from_get(
            state.clone(),
            &format!("/s3?key={query}&currentState=false"),
        )
        .await;
        assert_contains(s3_objects.results(), &entries, 0..2);
        assert_eq!(s3_objects.pagination().count, 2);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_filter_attributes(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap()
            .s3_objects;

        let result: ListResponse<S3> = response_from_get(
            state.clone(),
            "/s3?currentState=false&attributes[attributeId]=1",
        )
        .await;
        assert_eq!(result.results(), vec![entries[1].clone()]);
        assert_eq!(result.pagination().count, 1);

        let result: ListResponse<S3> = response_from_get(
            state.clone(),
            "/s3?currentState=false&attributes[nestedId][attributeId]=4",
        )
        .await;
        assert_eq!(result.results(), vec![entries[4].clone()]);
        assert_eq!(result.pagination().count, 1);

        let result: ListResponse<S3> = response_from_get(
            state.clone(),
            "/s3?currentState=false&attributes[nonExistentId]=1",
        )
        .await;
        assert!(result.results().is_empty());
        assert_eq!(result.pagination().count, 0);

        let result: ListResponse<S3> = response_from_get(
            state.clone(),
            "/s3?currentState=false&attributes[attributeId]=1&key=2",
        )
        .await;
        assert!(result.results().is_empty());
        assert_eq!(result.pagination().count, 0);

        let result: ListResponse<S3> = response_from_get(
            state.clone(),
            "/s3?currentState=false&attributes[attributeId]=1&key=1",
        )
        .await;
        assert_eq!(result.results(), vec![entries[1].clone()]);
        assert_eq!(result.pagination().count, 1);

        let result: ListResponse<S3> = response_from_get(
            state.clone(),
            "/s3?currentState=false&attributes[attributeId]=1&attributes[nestedId][attributeId]=1",
        )
        .await;
        assert_eq!(result.results(), vec![entries[1].clone()]);
        assert_eq!(result.pagination().count, 1);

        let result: ListResponse<S3> = response_from_get(
            state.clone(),
            "/s3?currentState=false&attributes[attributeId][]=1&attributes[attributeId][]=2",
        )
        .await;
        assert_eq!(
            result.results(),
            vec![entries[1].clone(), entries[2].clone()]
        );
        assert_eq!(result.pagination().count, 2);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn attributes_s3(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap()
            .s3_objects;

        let result: ListResponse<S3> = response_from_get(
            state.clone(),
            "/s3/attributes?currentState=false&attributeId=1",
        )
        .await;
        assert_eq!(result.results(), vec![entries[1].clone()]);
        assert_eq!(result.pagination().count, 1);

        let result: ListResponse<S3> = response_from_get(
            state.clone(),
            "/s3/attributes?currentState=false&nestedId[attributeId]=4",
        )
        .await;
        assert_eq!(result.results(), vec![entries[4].clone()]);
        assert_eq!(result.pagination().count, 1);

        let result: ListResponse<S3> = response_from_get(
            state.clone(),
            "/s3/attributes?currentState=false&nonExistentId=1",
        )
        .await;
        assert!(result.results().is_empty());
        assert_eq!(result.pagination().count, 0);

        let result: ListResponse<S3> = response_from_get(
            state.clone(),
            "/s3/attributes?currentState=false&attributeId=1&nonExistentId=2",
        )
        .await;
        assert!(result.results().is_empty());
        assert_eq!(result.pagination().count, 0);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_filter_attributes_wildcard(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let mut entries = EntriesBuilder::default()
            .build(state.database_client())
            .await
            .unwrap();

        change_many(
            state.database_client(),
            &entries,
            &[0, 1],
            Some(json!({"attributeId": "attributeId"})),
        )
        .await;

        entries_many(&mut entries, &[0, 1], json!({"attributeId": "attributeId"}));

        let s3_objects: ListResponse<S3> = response_from_get(
            state.clone(),
            "/s3?currentState=false&attributes[attributeId]=*a*",
        )
        .await;
        assert_contains(s3_objects.results(), &entries, 0..2);
        assert_eq!(s3_objects.pagination().count, 2);

        let s3_objects: ListResponse<S3> = response_from_get(
            state.clone(),
            "/s3?currentState=false&attributes[attributeId]=*A*",
        )
        .await;
        assert!(s3_objects.results().is_empty());
        assert_eq!(s3_objects.pagination().count, 0);

        let s3_objects: ListResponse<S3> = response_from_get(
            state.clone(),
            "/s3?currentState=false&attributes[attributeId]=*A*&caseSensitive=false",
        )
        .await;
        assert_contains(s3_objects.results(), &entries, 0..2);
        assert_eq!(s3_objects.pagination().count, 2);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_filter_escaped_attributes_wildcard(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let mut entries = EntriesBuilder::default()
            .build(state.database_client())
            .await
            .unwrap();

        change_many(
            state.database_client(),
            &entries,
            &[0, 1],
            Some(json!({ "attributeId": Uuid::default() })),
        )
        .await;
        entries_many(
            &mut entries,
            &[0, 1],
            json!({ "attributeId": Uuid::default() }),
        );

        let s3_objects: ListResponse<S3> = response_from_get(
            state.clone(),
            "/s3?currentState=false&attributes[attributeId]=????????-????-????-????-????????????",
        )
        .await;
        assert_contains(s3_objects.results(), &entries, 0..2);
        assert_eq!(s3_objects.pagination().count, 2);

        let s3_objects: ListResponse<S3> = response_from_get(
            state.clone(),
            "/s3?currentState=false&attributes[attributeId]=*-*-*-*-*",
        )
        .await;
        assert_contains(s3_objects.results(), &entries, 0..2);
        assert_eq!(s3_objects.pagination().count, 2);

        change_many(
            state.database_client(),
            &entries,
            &[0, 1],
            Some(json!({"attributeId": r"!$()*+.:<=>?[\]^{|}-"})),
        )
        .await;
        entries_many(
            &mut entries,
            &[0, 1],
            json!({"attributeId": r"!$()*+.:<=>?[\]^{|}-"}),
        );

        let query =
            percent_encode(r"!$()\*+.:<=>\?[\\]^{|}-".as_bytes(), NON_ALPHANUMERIC).to_string();
        let s3_objects: ListResponse<S3> = response_from_get(
            state.clone(),
            &format!("/s3?currentState=false&attributes[attributeId]={query}"),
        )
        .await;
        assert_contains(s3_objects.results(), &entries, 0..2);
        assert_eq!(s3_objects.pagination().count, 2);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn count_s3_api(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap();

        let result: ListCount = response_from_get(state, "/s3/count?currentState=false").await;
        assert_eq!(result.n_records, 10);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn count_s3_api_filter(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap();

        let result: ListCount =
            response_from_get(state, "/s3/count?currentState=false&bucket=0").await;
        assert_eq!(result.n_records, 2);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn count_s3_api_current_state(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        EntriesBuilder::default()
            .with_bucket_divisor(4)
            .with_key_divisor(3)
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap();

        let result: ListCount = response_from_get(state, "/s3/count").await;
        assert_eq!(result.n_records, 2);
    }

    pub(crate) fn mock_get_object(
        key: &'static str,
        bucket: &'static str,
        output: &'static [u8],
    ) -> Rule {
        mock!(aws_sdk_s3::Client::get_object)
            .match_requests(|req| req.bucket() == Some(bucket) && req.key() == Some(key))
            .then_output(move || {
                GetObjectOutput::builder()
                    .body(ByteStream::from_static(output))
                    .build()
            })
    }

    pub(crate) async fn response_from<T: DeserializeOwned>(
        state: AppState,
        uri: &str,
        method: Method,
        body: Body,
    ) -> (StatusCode, T) {
        let app = api_router(state).unwrap();
        let response = app
            .oneshot(
                Request::builder()
                    .method(method)
                    .uri(uri)
                    .header(HOST, "example.com")
                    .header(CONTENT_TYPE, "application/json")
                    .header(CONTENT_ENCODING, "gzip")
                    .body(body)
                    .unwrap(),
            )
            .await
            .unwrap();
        let status = response.status();

        let mut bytes = to_bytes(response.into_body(), usize::MAX)
            .await
            .unwrap()
            .to_vec();

        if bytes.is_empty() {
            bytes = "{}".as_bytes().to_vec();
        }

        println!("{}", String::from_utf8(bytes.clone()).unwrap());

        (status, from_slice::<T>(bytes.as_slice()).unwrap())
    }

    pub(crate) async fn response_from_get<T: DeserializeOwned>(state: AppState, uri: &str) -> T {
        response_from(state, uri, Method::GET, Body::empty())
            .await
            .1
    }
}
