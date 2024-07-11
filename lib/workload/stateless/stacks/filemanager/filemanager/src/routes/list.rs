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
use crate::routes::filtering::{ObjectsFilterAll, S3ObjectsFilterAll};
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
    params(Pagination, ObjectsFilterAll),
    context_path = "/api/v1",
)]
pub async fn list_objects(
    state: State<AppState>,
    Query(pagination): Query<Pagination>,
    QsQuery(filter_all): QsQuery<ObjectsFilterAll>,
) -> Result<Json<ListResponse<FileObject>>> {
    let response = ListQueryBuilder::<ObjectEntity>::new(&state.client)
        .filter_all(filter_all)
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
    params(Pagination, S3ObjectsFilterAll),
    context_path = "/api/v1",
)]
pub async fn list_s3_objects(
    state: State<AppState>,
    Query(pagination): Query<Pagination>,
    QsQuery(filter_all): QsQuery<S3ObjectsFilterAll>,
) -> Result<Json<ListResponse<FileS3Object>>> {
    let response = ListQueryBuilder::<S3ObjectEntity>::new(&state.client)
        .filter_all(filter_all)
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
pub(crate) mod tests {
    use axum::body::to_bytes;
    use axum::body::Body;
    use axum::http::Request;
    use serde::de::DeserializeOwned;
    use serde_json::from_slice;
    use sqlx::PgPool;
    use tower::ServiceExt;

    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::entities::object::Model as Object;
    use crate::database::entities::s3_object::Model as S3Object;
    use crate::database::entities::sea_orm_active_enums::EventType;
    use crate::queries::tests::{initialize_database, initialize_database_reorder};
    use crate::routes::api_router;

    use super::*;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_objects_api(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = initialize_database(state.client(), 10).await.objects;

        let result: ListResponse<Object> = response_from(state, "/objects").await;
        assert!(result.next_page.is_none());
        assert_eq!(result.results, entries);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_objects_api_filter_attributes(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = initialize_database(state.client(), 10).await.objects;

        let result: ListResponse<Object> =
            response_from(state.clone(), "/objects?attributes[attribute_id]=1").await;
        assert_eq!(result.results, vec![entries[1].clone()]);

        let result: ListResponse<Object> = response_from(
            state.clone(),
            "/objects?attributes[nested_id][attribute_id]=2",
        )
        .await;
        assert_eq!(result.results, vec![entries[2].clone()]);

        let result: ListResponse<Object> =
            response_from(state.clone(), "/objects?attributes[non_existent_id]=1").await;
        assert!(result.results.is_empty());
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_objects_api(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = initialize_database_reorder(state.client(), 10)
            .await
            .s3_objects;

        let result: ListResponse<S3Object> = response_from(state, "/s3_objects").await;
        assert!(result.next_page.is_none());
        assert_eq!(result.results, entries);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_objects_filter_event_type(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = initialize_database(state.client(), 10).await.s3_objects;

        let result: ListResponse<S3Object> =
            response_from(state, "/s3_objects?event_type=Deleted").await;
        assert_eq!(result.results().len(), 5);
        assert_eq!(
            result.results,
            entries
                .into_iter()
                .filter(|entry| entry.event_type == EventType::Deleted)
                .collect::<Vec<_>>()
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_objects_multiple_filters(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = initialize_database(state.client(), 10).await.s3_objects;

        let result: ListResponse<S3Object> =
            response_from(state, "/s3_objects?bucket=1&key=2").await;
        assert_eq!(result.results, vec![entries[2].clone()]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_objects_filter_attributes(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = initialize_database(state.client(), 10).await.s3_objects;

        let result: ListResponse<S3Object> =
            response_from(state.clone(), "/s3_objects?attributes[attribute_id]=1").await;
        assert_eq!(result.results, vec![entries[1].clone()]);

        let result: ListResponse<S3Object> = response_from(
            state.clone(),
            "/s3_objects?attributes[nested_id][attribute_id]=4",
        )
        .await;
        assert_eq!(result.results, vec![entries[4].clone()]);

        let result: ListResponse<S3Object> =
            response_from(state.clone(), "/s3_objects?attributes[non_existent_id]=1").await;
        assert!(result.results.is_empty());

        let result: ListResponse<S3Object> = response_from(
            state.clone(),
            "/s3_objects?attributes[attribute_id]=1&key=2",
        )
        .await;
        assert!(result.results.is_empty());

        let result: ListResponse<S3Object> =
            response_from(state, "/s3_objects?attributes[attribute_id]=1&key=1").await;
        assert_eq!(result.results, vec![entries[1].clone()]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn count_objects_api(pool: PgPool) {
        let state = AppState::from_pool(pool);
        initialize_database(state.client(), 10).await;

        let result: ListCount = response_from(state, "/objects/count").await;
        assert_eq!(result.n_records, 10);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn count_s3_objects_api(pool: PgPool) {
        let state = AppState::from_pool(pool);
        initialize_database(state.client(), 10).await;

        let result: ListCount = response_from(state, "/s3_objects/count").await;
        assert_eq!(result.n_records, 10);
    }

    pub(crate) async fn response_from<T: DeserializeOwned>(state: AppState, uri: &str) -> T {
        let app = api_router(state);
        let response = app
            .oneshot(Request::builder().uri(uri).body(Body::empty()).unwrap())
            .await
            .unwrap();

        let bytes = to_bytes(response.into_body(), usize::MAX)
            .await
            .unwrap()
            .to_vec();
        from_slice::<T>(bytes.as_slice()).unwrap()
    }
}
