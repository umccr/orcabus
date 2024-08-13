//! Route logic for list API calls.
//!

use crate::database::entities::s3_object;
use crate::database::entities::s3_object::Model as S3;
use crate::error::Error::{MissingHostHeader, ParseError};
use crate::error::Result;
use crate::queries::list::ListQueryBuilder;
use crate::routes::error::ErrorStatusCode;
use crate::routes::filter::S3ObjectsFilter;
use crate::routes::pagination::{ListResponse, Pagination};
use crate::routes::AppState;
use axum::extract::{Query, Request, State};
use axum::http::header::HOST;
use axum::routing::get;
use axum::{Json, Router};
use serde::{Deserialize, Serialize};
use serde_qs::axum::QsQuery;
use url::Url;
use utoipa::{IntoParams, ToSchema};

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
#[derive(Debug, Deserialize, Default, IntoParams)]
#[serde(default, rename_all = "camelCase")]
#[into_params(parameter_in = Query)]
pub struct WildcardParams {
    /// The case sensitivity when using filter operations with a wildcard.
    /// Setting this true means that an SQL `like` statement is used, and false
    /// means `ilike` is used.
    #[serde(default = "default_case_sensitivity")]
    #[param(nullable, default = true)]
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

/// Params for a list s3 objects request.
#[derive(Debug, Deserialize, Default, IntoParams)]
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
    #[param(nullable, default = false)]
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
        (status = OK, description = "The collection of s3_objects", body = ListResponseS3),
        ErrorStatusCode,
    ),
    params(Pagination, WildcardParams, ListS3Params, S3ObjectsFilter),
    context_path = "/api/v1",
    tag = "list",
)]
pub async fn list_s3(
    state: State<AppState>,
    Query(pagination): Query<Pagination>,
    Query(wildcard): Query<WildcardParams>,
    Query(list): Query<ListS3Params>,
    QsQuery(filter_all): QsQuery<S3ObjectsFilter>,
    request: Request,
) -> Result<Json<ListResponse<S3>>> {
    let mut response = ListQueryBuilder::<_, s3_object::Entity>::new(state.client.connection_ref())
        .filter_all(filter_all, wildcard.case_sensitive());

    if list.current_state {
        response = response.current_state();
    }

    let host: Url = request
        .headers()
        .get(HOST)
        .ok_or_else(|| MissingHostHeader)?
        .to_str()
        .map_err(|err| ParseError(err.to_string()))?
        .parse()?;
    let url = host.join(&request.uri().to_string())?;

    Ok(Json(
        response.paginate_to_list_response(pagination, url).await?,
    ))
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
    Query(wildcard): Query<WildcardParams>,
    Query(list): Query<ListS3Params>,
    QsQuery(filter_all): QsQuery<S3ObjectsFilter>,
) -> Result<Json<ListCount>> {
    let mut response = ListQueryBuilder::<_, s3_object::Entity>::new(state.client.connection_ref())
        .filter_all(filter_all, wildcard.case_sensitive());

    if list.current_state {
        response = response.current_state();
    }

    Ok(Json(response.to_list_count().await?))
}

/// The router for list objects.
pub fn list_router() -> Router<AppState> {
    Router::new()
        .route("/s3", get(list_s3))
        .route("/s3/count", get(count_s3))
}

#[cfg(test)]
pub(crate) mod tests {
    use axum::body::to_bytes;
    use axum::body::Body;
    use axum::http::header::CONTENT_TYPE;
    use axum::http::{Method, Request, StatusCode};
    use serde::de::DeserializeOwned;
    use serde_json::{from_slice, json};
    use sqlx::PgPool;
    use tower::ServiceExt;

    use super::*;
    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::entities::sea_orm_active_enums::EventType;
    use crate::queries::list::tests::filter_event_type;
    use crate::queries::update::tests::change_many;
    use crate::queries::update::tests::{assert_contains, entries_many};
    use crate::queries::EntriesBuilder;
    use crate::routes::api_router;
    use crate::routes::pagination::Links;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_api(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.client())
            .await
            .s3_objects;

        let result: ListResponse<S3> = response_from_get(state, "/s3").await;
        assert_eq!(result.links(), &Links::new(None, None));
        assert_eq!(result.results(), entries);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_current_s3_paginate(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_bucket_divisor(4)
            .with_key_divisor(3)
            .with_shuffle(true)
            .build(state.client())
            .await
            .s3_objects;

        let result: ListResponse<S3> =
            response_from_get(state, "/s3?currentState=true&rowsPerPage=1&page=0").await;
        assert_eq!(
            result.links(),
            &Links::new(
                None,
                Some(
                    "https://example.com/s3?currentState=true&rowsPerPage=1&page=1"
                        .parse()
                        .unwrap()
                )
            )
        );
        assert_eq!(result.results(), vec![entries[2].clone()]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_current_s3_filter(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_n(30)
            .with_bucket_divisor(8)
            .with_key_divisor(5)
            .build(state.client())
            .await
            .s3_objects;

        let result: ListResponse<S3> =
            response_from_get(state, "/s3?currentState=true&size=4&rowsPerPage=1&page=0").await;
        assert_eq!(result.links(), &Links::new(None, None));
        assert_eq!(result.results(), vec![entries[24].clone()]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_filter_event_type(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.client())
            .await
            .s3_objects;

        let result: ListResponse<S3> = response_from_get(state, "/s3?eventType=Deleted").await;
        assert_eq!(result.results().len(), 5);
        assert_eq!(
            result.results(),
            filter_event_type(entries, EventType::Deleted)
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_multiple_filters(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.client())
            .await
            .s3_objects;

        let result: ListResponse<S3> = response_from_get(state, "/s3?bucket=1&key=2").await;
        assert_eq!(result.results(), vec![entries[2].clone()]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_filter_attributes(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.client())
            .await
            .s3_objects;

        let result: ListResponse<S3> =
            response_from_get(state.clone(), "/s3?attributes[attributeId]=1").await;
        assert_eq!(result.results(), vec![entries[1].clone()]);

        let result: ListResponse<S3> =
            response_from_get(state.clone(), "/s3?attributes[nestedId][attributeId]=4").await;
        assert_eq!(result.results(), vec![entries[4].clone()]);

        let result: ListResponse<S3> =
            response_from_get(state.clone(), "/s3?attributes[nonExistentId]=1").await;
        assert!(result.results().is_empty());

        let result: ListResponse<S3> =
            response_from_get(state.clone(), "/s3?attributes[attributeId]=1&key=2").await;
        assert!(result.results().is_empty());

        let result: ListResponse<S3> =
            response_from_get(state, "/s3?attributes[attributeId]=1&key=1").await;
        assert_eq!(result.results(), vec![entries[1].clone()]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_filter_attributes_wildcard(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(state.client()).await;

        change_many(
            state.client(),
            &entries,
            &[0, 1],
            Some(json!({"attributeId": "attributeId"})),
        )
        .await;

        entries_many(&mut entries, &[0, 1], json!({"attributeId": "attributeId"}));

        let s3_objects: ListResponse<S3> =
            response_from_get(state.clone(), "/s3?attributes[attributeId]=%a%").await;
        assert_contains(s3_objects.results(), &entries, 0..2);

        let s3_objects: ListResponse<S3> =
            response_from_get(state.clone(), "/s3?attributes[attributeId]=%A%").await;
        assert!(s3_objects.results().is_empty());

        let s3_objects: ListResponse<S3> = response_from_get(
            state.clone(),
            "/s3?attributes[attributeId]=%A%&caseSensitive=false",
        )
        .await;
        assert_contains(s3_objects.results(), &entries, 0..2);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn count_s3_api(pool: PgPool) {
        let state = AppState::from_pool(pool);
        EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.client())
            .await;

        let result: ListCount = response_from_get(state, "/s3/count").await;
        assert_eq!(result.n_records, 10);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn count_s3_api_filter(pool: PgPool) {
        let state = AppState::from_pool(pool);
        EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.client())
            .await;

        let result: ListCount = response_from_get(state, "/s3/count?bucket=0").await;
        assert_eq!(result.n_records, 2);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn count_s3_api_current_state(pool: PgPool) {
        let state = AppState::from_pool(pool);
        EntriesBuilder::default()
            .with_bucket_divisor(4)
            .with_key_divisor(3)
            .with_shuffle(true)
            .build(state.client())
            .await;

        let result: ListCount = response_from_get(state, "/s3/count?currentState=true").await;
        assert_eq!(result.n_records, 2);
    }

    pub(crate) async fn response_from<T: DeserializeOwned>(
        state: AppState,
        uri: &str,
        method: Method,
        body: Body,
    ) -> (StatusCode, T) {
        let app = api_router(state);
        let response = app
            .oneshot(
                Request::builder()
                    .method(method)
                    .uri(uri)
                    .header(HOST, "https://example.com")
                    .header(CONTENT_TYPE, "application/json")
                    .body(body)
                    .unwrap(),
            )
            .await
            .unwrap();
        let status = response.status();

        let bytes = to_bytes(response.into_body(), usize::MAX)
            .await
            .unwrap()
            .to_vec();

        (status, from_slice::<T>(bytes.as_slice()).unwrap())
    }

    pub(crate) async fn response_from_get<T: DeserializeOwned>(state: AppState, uri: &str) -> T {
        response_from(state, uri, Method::GET, Body::empty())
            .await
            .1
    }
}
