//! Route logic for list API calls.
//!

use axum::extract::{Query, State};
use axum::Json;
use serde::{Deserialize, Serialize};
use serde_qs::axum::QsQuery;
use utoipa::ToSchema;

use crate::database::entities::object::Entity as ObjectEntity;
use crate::database::entities::object::Model as FileObject;
use crate::database::entities::s3_object::Entity as S3ObjectEntity;
use crate::database::entities::s3_object::Model as FileS3Object;
use crate::error::Result;
use crate::queries::list::ListQueryBuilder;
use crate::routes::filtering::{ObjectsFilterByAll, S3ObjectsFilterByAll};
use crate::routes::pagination::Pagination;
use crate::routes::{AppState, ErrorStatusCode};

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

/// Params for a list objects request.
#[derive(Debug, Deserialize)]
pub struct ListObjectsParams {}

/// The response type for list operations.
#[derive(Debug, Deserialize, Serialize, ToSchema, Eq, PartialEq)]
#[aliases(ListResponseObject = ListResponse<FileObject>, ListResponseS3Object = ListResponse<FileS3Object>)]
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

/// The list objects handler.
#[utoipa::path(
    get,
    path = "/objects",
    responses(
        (status = OK, description = "List all objects", body = Vec<FileObject>),
        ErrorStatusCode,
    ),
    params(Pagination, ObjectsFilterByAll),
    context_path = "/api/v1",
)]
pub async fn list_objects(
    state: State<AppState>,
    Query(pagination): Query<Pagination>,
    QsQuery(filter_by_all): QsQuery<ObjectsFilterByAll>,
) -> Result<Json<ListResponse<FileObject>>> {
    let response = ListQueryBuilder::<ObjectEntity>::new(&state.client)
        .filter_all(filter_by_all)
        .await
        .paginate_to_list_response(pagination)
        .await?;

    Ok(Json(response))
}

/// The count objects handler.
#[utoipa::path(
    get,
    path = "/objects/count",
    responses(
        (status = OK, description = "Get the count of all objects", body = ListCount),
        ErrorStatusCode,
    ),
    context_path = "/api/v1",
)]
pub async fn count_objects(state: State<AppState>) -> Result<Json<ListCount>> {
    let response = ListQueryBuilder::<ObjectEntity>::new(&state.client)
        .to_list_count()
        .await?;

    Ok(Json(response))
}

/// Params for a list s3 objects request.
#[derive(Debug, Deserialize)]
pub struct ListS3ObjectsParams {}

/// The list s3 objects handler.
#[utoipa::path(
    get,
    path = "/s3_objects",
    responses(
        (status = OK, description = "List all s3 objects", body = Vec<FileS3Object>),
        ErrorStatusCode,
    ),
    params(Pagination, S3ObjectsFilterByAll),
    context_path = "/api/v1",
)]
pub async fn list_s3_objects(
    state: State<AppState>,
    Query(pagination): Query<Pagination>,
    QsQuery(filter_by_all): QsQuery<S3ObjectsFilterByAll>,
) -> Result<Json<ListResponse<FileS3Object>>> {
    let response = ListQueryBuilder::<S3ObjectEntity>::new(&state.client)
        .filter_all(filter_by_all)
        .await
        .paginate_to_list_response(pagination)
        .await?;

    Ok(Json(response))
}

/// The count s3 objects handler.
#[utoipa::path(
    get,
    path = "/s3_objects/count",
    responses(
        (status = OK, description = "Get the count of all s3 objects", body = ListCount),
        ErrorStatusCode,
    ),
    context_path = "/api/v1",
)]
pub async fn count_s3_objects(state: State<AppState>) -> Result<Json<ListCount>> {
    let response = ListQueryBuilder::<S3ObjectEntity>::new(&state.client)
        .to_list_count()
        .await?;

    Ok(Json(response))
}

#[cfg(test)]
mod tests {
    use axum::body::to_bytes;
    use axum::body::Body;
    use axum::http::Request;
    use parquet::data_type::AsBytes;
    use serde_json::from_slice;
    use sqlx::PgPool;
    use tower::ServiceExt;

    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::entities::object::Model as Object;
    use crate::database::entities::s3_object::Model as S3Object;
    use crate::queries::tests::{initialize_database, initialize_database_reorder};
    use crate::routes::list::{ListCount, ListResponse};
    use crate::routes::{api_router, AppState};

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_objects_api(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = initialize_database(state.client(), 10).await;

        let app = api_router(state);
        let response = app
            .oneshot(
                Request::builder()
                    .uri("/objects")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        let result = from_slice::<ListResponse<Object>>(
            to_bytes(response.into_body(), usize::MAX)
                .await
                .unwrap()
                .as_bytes(),
        )
        .unwrap();

        assert!(result.next_page.is_none());
        assert_eq!(
            result.results,
            entries
                .into_iter()
                .map(|(entry, _)| entry)
                .collect::<Vec<_>>()
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_objects_api(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = initialize_database_reorder(state.client(), 10).await;

        let app = api_router(state);
        let response = app
            .oneshot(
                Request::builder()
                    .uri("/s3_objects")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        let result = from_slice::<ListResponse<S3Object>>(
            to_bytes(response.into_body(), usize::MAX)
                .await
                .unwrap()
                .as_bytes(),
        )
        .unwrap();

        assert!(result.next_page.is_none());
        assert_eq!(
            result.results,
            entries
                .into_iter()
                .map(|(_, entry)| entry)
                .collect::<Vec<_>>()
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn count_objects_api(pool: PgPool) {
        let state = AppState::from_pool(pool);
        initialize_database(state.client(), 10).await;

        let app = api_router(state);
        let response = app
            .oneshot(
                Request::builder()
                    .uri("/objects/count")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        let result = from_slice::<ListCount>(
            to_bytes(response.into_body(), usize::MAX)
                .await
                .unwrap()
                .as_bytes(),
        )
        .unwrap();

        assert_eq!(result.n_records, 10);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn count_s3_objects_api(pool: PgPool) {
        let state = AppState::from_pool(pool);
        initialize_database(state.client(), 10).await;

        let app = api_router(state);
        let response = app
            .oneshot(
                Request::builder()
                    .uri("/s3_objects/count")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        let result = from_slice::<ListCount>(
            to_bytes(response.into_body(), usize::MAX)
                .await
                .unwrap()
                .as_bytes(),
        )
        .unwrap();

        assert_eq!(result.n_records, 10);
    }
}
