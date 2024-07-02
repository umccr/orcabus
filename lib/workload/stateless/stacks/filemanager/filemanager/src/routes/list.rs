//! Route logic for list API calls.
//!

use axum::extract::State;
use axum::Json;
use serde::Deserialize;

use crate::database::entities::object::Model as FileObject;
use crate::database::entities::s3_object::Model as FileS3Object;
use crate::error::Result;
use crate::queries::list::ListQueryBuilder;
use crate::routes::{AppState, ErrorStatusCode};

/// Params for a list objects request.
#[derive(Debug, Deserialize)]
pub struct ListObjectsParams {}

/// The list objects handler.
#[utoipa::path(
    get,
    path = "/objects",
    responses(
        (status = OK, description = "List all objects", body = Vec<FileObject>),
        ErrorStatusCode,
    ),
    context_path = "/file/v1",
)]
pub async fn list_objects(state: State<AppState>) -> Result<Json<Vec<FileObject>>> {
    let query = ListQueryBuilder::new(&state.client);

    Ok(Json(query.list_objects().await?))
}

/// The count objects handler.
#[utoipa::path(
    get,
    path = "/objects/count",
    responses(
        (status = OK, description = "Get the count of all objects", body = u64),
        ErrorStatusCode,
    ),
    context_path = "/file/v1",
)]
pub async fn count_objects(state: State<AppState>) -> Result<Json<u64>> {
    let query = ListQueryBuilder::new(&state.client);

    Ok(Json(query.count_objects().await?))
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
    context_path = "/file/v1",
)]
pub async fn list_s3_objects(state: State<AppState>) -> Result<Json<Vec<FileS3Object>>> {
    let query = ListQueryBuilder::new(&state.client);

    Ok(Json(query.list_s3_objects().await?))
}

/// The count s3 objects handler.
#[utoipa::path(
    get,
    path = "/s3_objects/count",
    responses(
        (status = OK, description = "Get the count of all s3 objects", body = u64),
        ErrorStatusCode,
    ),
    context_path = "/file/v1",
)]
pub async fn count_s3_objects(state: State<AppState>) -> Result<Json<u64>> {
    let query = ListQueryBuilder::new(&state.client);

    Ok(Json(query.count_s3_objects().await?))
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

        let result = from_slice::<Vec<Object>>(
            to_bytes(response.into_body(), usize::MAX)
                .await
                .unwrap()
                .as_bytes(),
        )
        .unwrap();

        assert_eq!(
            result,
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

        let result = from_slice::<Vec<S3Object>>(
            to_bytes(response.into_body(), usize::MAX)
                .await
                .unwrap()
                .as_bytes(),
        )
        .unwrap();

        assert_eq!(
            result,
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

        let result = from_slice::<u64>(
            to_bytes(response.into_body(), usize::MAX)
                .await
                .unwrap()
                .as_bytes(),
        )
        .unwrap();

        assert_eq!(result, 10);
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

        let result = from_slice::<u64>(
            to_bytes(response.into_body(), usize::MAX)
                .await
                .unwrap()
                .as_bytes(),
        )
        .unwrap();

        assert_eq!(result, 10);
    }
}
