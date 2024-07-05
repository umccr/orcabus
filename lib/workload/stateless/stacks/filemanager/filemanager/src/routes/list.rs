//! Route logic for list API calls.
//!

use axum::extract::{Query, State};
use axum::Json;
use serde::{Deserialize, Deserializer, Serialize};
use std::result;
use utoipa::ToSchema;

use crate::database::entities::object::Entity as ObjectEntity;
use crate::database::entities::object::Model as FileObject;
use crate::database::entities::s3_object::Entity as S3ObjectEntity;
use crate::database::entities::s3_object::Model as FileS3Object;
use crate::error::Result;
use crate::queries::list::ListQueryBuilder;
use crate::routes::{AppState, ErrorStatusCode};

/// The return value for count operations showing the number of records in the database.
#[derive(Debug, Deserialize, Serialize, ToSchema)]
pub struct ListCount {
    /// The number of records.
    n_records: u64,
}

impl ListCount {
    /// Create a new list count.
    pub fn new(n_records: u64) -> Self {
        ListCount { n_records }
    }
}

/// Params for a list objects request.
#[derive(Debug, Deserialize)]
pub struct ListObjectsParams {}

/// Pagination query parameters for list operations.
#[derive(Debug, Deserialize, ToSchema)]
#[serde(default)]
pub struct Pagination {
    /// The zero-indexed page to fetch from the list of objects.
    /// Increments by 1 starting from 0.
    /// Defaults to the beginning of the collection.
    pub(crate) page: u64,
    /// The page to fetch from the list of objects.
    /// Defaults to 1000.
    /// If this is zero then the default is used.
    #[serde(deserialize_with = "deserialize_zero_page_as_default")]
    pub(crate) page_size: u64,
}

/// The default page size.
fn default_page_size() -> u64 {
    1000
}

/// Deserializer to convert a 0 value to the default pagination size.
fn deserialize_zero_page_as_default<'de, D>(deserializer: D) -> result::Result<u64, D::Error>
where
    D: Deserializer<'de>,
{
    let value: u64 = Deserialize::deserialize(deserializer)?;
    if value == 0 {
        Ok(default_page_size())
    } else {
        Ok(value)
    }
}

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
}

impl Default for Pagination {
    fn default() -> Self {
        Self {
            page: 0,
            page_size: default_page_size(),
        }
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
    context_path = "/api/v1",
)]
pub async fn list_objects(
    state: State<AppState>,
    Query(pagination): Query<Pagination>,
) -> Result<Json<ListResponse<FileObject>>> {
    let response = ListQueryBuilder::<ObjectEntity>::new(&state.client)
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
    context_path = "/api/v1",
)]
pub async fn list_s3_objects(
    state: State<AppState>,
    Query(pagination): Query<Pagination>,
) -> Result<Json<ListResponse<FileS3Object>>> {
    let response = ListQueryBuilder::<S3ObjectEntity>::new(&state.client)
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
    use crate::queries::tests::initialize_database;
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
    async fn list_objects_api_paginate(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = initialize_database(state.client(), 10).await;

        let app = api_router(state);
        let response = app
            .oneshot(
                Request::builder()
                    .uri("/objects?page=1&page_size=2")
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

        assert_eq!(result.next_page, Some(2));
        assert_eq!(
            result.results,
            entries
                .into_iter()
                .map(|(entry, _)| entry)
                .collect::<Vec<_>>()[2..4]
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_objects_api_zero_page_size(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = initialize_database(state.client(), 10).await;

        let app = api_router(state);
        let response = app
            .oneshot(
                Request::builder()
                    .uri("/s3_objects?page_size=0")
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

        assert_eq!(result.next_page, None);
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
        let entries = initialize_database(state.client(), 10).await;

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
    async fn list_s3_objects_api_paginate(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = initialize_database(state.client(), 10).await;

        let app = api_router(state);
        let response = app
            .oneshot(
                Request::builder()
                    .uri("/s3_objects?page=1&page_size=2")
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

        assert_eq!(result.next_page, Some(2));
        assert_eq!(
            result.results,
            entries
                .into_iter()
                .map(|(_, entry)| entry)
                .collect::<Vec<_>>()[2..4]
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_objects_api_zero_page_size(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = initialize_database(state.client(), 10).await;

        let app = api_router(state);
        let response = app
            .oneshot(
                Request::builder()
                    .uri("/s3_objects?page_size=0")
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

        assert_eq!(result.next_page, None);
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
