//! Route logic for list API calls.
//!

use crate::database::entities::s3_object;
use crate::database::entities::s3_object::Model as FileS3Object;
use crate::error::Result;
use crate::queries::list::ListQueryBuilder;
use crate::routes::error::ErrorStatusCode;
use crate::routes::filter::S3ObjectsFilter;
use crate::routes::pagination::Pagination;
use crate::routes::AppState;
use axum::extract::{Query, State};
use axum::routing::get;
use axum::{Json, Router};
use serde::{Deserialize, Serialize};
use serde_qs::axum::QsQuery;
use utoipa::{IntoParams, ToSchema};

/// The return value for count operations showing the number of records in the database.
#[derive(Debug, Deserialize, Serialize, ToSchema, Eq, PartialEq)]
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

/// The response type for list operations.
#[derive(Debug, Deserialize, Serialize, ToSchema, Eq, PartialEq)]
#[aliases(ListResponseS3Object = ListResponse<FileS3Object>)]
pub struct ListResponse<M> {
    /// The results of the list operation.
    results: Vec<M>,
    /// The next page if fetching additional pages. Increments by 1 from 0.
    /// Use this as the `page` parameter in the next request if fetching additional pages.
    /// Empty if there are no more objects available in the collection.
    next_page: Option<u64>,
}

impl<M> ListResponse<M> {
    /// Create a new list response.
    pub fn new(results: Vec<M>, next_page: Option<u64>) -> Self {
        ListResponse { results, next_page }
    }

    /// Get the results.
    pub fn results(&self) -> &[M] {
        &self.results
    }

    /// Get the next page.
    pub fn next_page(&self) -> Option<u64> {
        self.next_page
    }
}

/// Params for wildcard requests.
#[derive(Debug, Deserialize, Default, IntoParams)]
#[serde(default)]
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
#[serde(default)]
#[into_params(parameter_in = Query)]
pub struct ListS3ObjectsParams {
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

impl ListS3ObjectsParams {
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
    path = "/s3_objects",
    responses(
        (status = OK, description = "The collection of s3_objects", body = ListResponseS3Object),
        ErrorStatusCode,
    ),
    params(Pagination, WildcardParams, ListS3ObjectsParams, S3ObjectsFilter),
    context_path = "/api/v1",
    tag = "list",
)]
pub async fn list_s3_objects(
    state: State<AppState>,
    Query(pagination): Query<Pagination>,
    Query(wildcard): Query<WildcardParams>,
    Query(list): Query<ListS3ObjectsParams>,
    QsQuery(filter_all): QsQuery<S3ObjectsFilter>,
) -> Result<Json<ListResponse<FileS3Object>>> {
    let mut response = ListQueryBuilder::<_, s3_object::Entity>::new(state.client.connection_ref())
        .filter_all(filter_all, wildcard.case_sensitive());

    if list.current_state {
        response = response.current_state();
    }

    Ok(Json(response.paginate_to_list_response(pagination).await?))
}

/// Count all s3_objects according to the parameters.
#[utoipa::path(
    get,
    path = "/s3_objects/count",
    responses(
        (status = OK, description = "The count of s3 objects", body = ListCount),
        ErrorStatusCode,
    ),
    params(WildcardParams, ListS3ObjectsParams, S3ObjectsFilter),
    context_path = "/api/v1",
    tag = "list",
)]
pub async fn count_s3_objects(
    state: State<AppState>,
    Query(wildcard): Query<WildcardParams>,
    Query(list): Query<ListS3ObjectsParams>,
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
        .route("/s3_objects", get(list_s3_objects))
        .route("/s3_objects/count", get(count_s3_objects))
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

    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::entities::sea_orm_active_enums::EventType;
    use crate::queries::list::tests::filter_event_type;
    use crate::queries::update::tests::change_many;
    use crate::queries::update::tests::{assert_contains, entries_many};
    use crate::queries::EntriesBuilder;
    use crate::routes::api_router;

    use super::*;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_objects_api(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.client())
            .await
            .s3_objects;

        let result: ListResponse<FileS3Object> = response_from_get(state, "/s3_objects").await;
        assert!(result.next_page.is_none());
        assert_eq!(result.results, entries);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_current_s3_objects_paginate(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_bucket_divisor(4)
            .with_key_divisor(3)
            .with_shuffle(true)
            .build(state.client())
            .await
            .s3_objects;

        let result: ListResponse<FileS3Object> =
            response_from_get(state, "/s3_objects?current_state=true&page_size=1&page=0").await;
        assert_eq!(result.next_page, Some(1));
        assert_eq!(result.results, vec![entries[2].clone()]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_current_s3_objects_filter(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_n(30)
            .with_bucket_divisor(8)
            .with_key_divisor(5)
            .build(state.client())
            .await
            .s3_objects;

        let result: ListResponse<FileS3Object> = response_from_get(
            state,
            "/s3_objects?current_state=true&size=4&page_size=1&page=0",
        )
        .await;
        assert!(result.next_page.is_none());
        assert_eq!(result.results, vec![entries[24].clone()]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_objects_filter_event_type(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.client())
            .await
            .s3_objects;

        let result: ListResponse<FileS3Object> =
            response_from_get(state, "/s3_objects?event_type=Deleted").await;
        assert_eq!(result.results().len(), 5);
        assert_eq!(
            result.results,
            filter_event_type(entries, EventType::Deleted)
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_objects_multiple_filters(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.client())
            .await
            .s3_objects;

        let result: ListResponse<FileS3Object> =
            response_from_get(state, "/s3_objects?bucket=1&key=2").await;
        assert_eq!(result.results, vec![entries[2].clone()]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_objects_filter_attributes(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.client())
            .await
            .s3_objects;

        let result: ListResponse<FileS3Object> =
            response_from_get(state.clone(), "/s3_objects?attributes[attribute_id]=1").await;
        assert_eq!(result.results, vec![entries[1].clone()]);

        let result: ListResponse<FileS3Object> = response_from_get(
            state.clone(),
            "/s3_objects?attributes[nested_id][attribute_id]=4",
        )
        .await;
        assert_eq!(result.results, vec![entries[4].clone()]);

        let result: ListResponse<FileS3Object> =
            response_from_get(state.clone(), "/s3_objects?attributes[non_existent_id]=1").await;
        assert!(result.results.is_empty());

        let result: ListResponse<FileS3Object> = response_from_get(
            state.clone(),
            "/s3_objects?attributes[attribute_id]=1&key=2",
        )
        .await;
        assert!(result.results.is_empty());

        let result: ListResponse<FileS3Object> =
            response_from_get(state, "/s3_objects?attributes[attribute_id]=1&key=1").await;
        assert_eq!(result.results, vec![entries[1].clone()]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_objects_filter_attributes(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(state.client()).await;

        change_many(
            state.client(),
            &entries,
            &[0, 1],
            Some(json!({"attribute_id": "attribute_id"})),
        )
        .await;

        entries_many(
            &mut entries,
            &[0, 1],
            json!({"attribute_id": "attribute_id"}),
        );

        let s3_objects: ListResponse<FileS3Object> =
            response_from_get(state.clone(), "/s3_objects?attributes[attribute_id]=%a%").await;
        assert_contains(&s3_objects.results, &entries, 0..2);

        let s3_objects: ListResponse<FileS3Object> =
            response_from_get(state.clone(), "/s3_objects?attributes[attribute_id]=%A%").await;
        assert!(s3_objects.results.is_empty());

        let s3_objects: ListResponse<FileS3Object> = response_from_get(
            state.clone(),
            "/s3_objects?attributes[attribute_id]=%A%&case_sensitive=false",
        )
        .await;
        assert_contains(&s3_objects.results, &entries, 0..2);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn count_s3_objects_api(pool: PgPool) {
        let state = AppState::from_pool(pool);
        EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.client())
            .await;

        let result: ListCount = response_from_get(state, "/s3_objects/count").await;
        assert_eq!(result.n_records, 10);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn count_s3_objects_api_filter(pool: PgPool) {
        let state = AppState::from_pool(pool);
        EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.client())
            .await;

        let result: ListCount = response_from_get(state, "/s3_objects/count?bucket=0").await;
        assert_eq!(result.n_records, 2);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn count_s3_objects_api_current_state(pool: PgPool) {
        let state = AppState::from_pool(pool);
        EntriesBuilder::default()
            .with_bucket_divisor(4)
            .with_key_divisor(3)
            .with_shuffle(true)
            .build(state.client())
            .await;

        let result: ListCount =
            response_from_get(state, "/s3_objects/count?current_state=true").await;
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
