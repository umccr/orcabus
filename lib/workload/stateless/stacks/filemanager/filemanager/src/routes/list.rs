//! Route logic for list API calls.
//!

use axum::extract::State;
use axum::Json;
use serde::Deserialize;

use crate::database::entities::object_group::Model as ObjectGroup;
use crate::database::entities::s3_object::Model as S3Object;
use crate::error::Result;
use crate::queries::list::ListQueryBuilder;
use crate::routes::AppState;

/// Params for a list object groups request.
#[derive(Debug, Deserialize)]
pub struct ListObjectGroupsParams {}

/// The list object groups handler.
pub async fn list_object_groups(state: State<AppState>) -> Result<Json<Vec<ObjectGroup>>> {
    let query = ListQueryBuilder::new(&state.client);

    Ok(Json(query.list_object_groups().await?))
}

/// The count object groups handler.
pub async fn count_object_groups(state: State<AppState>) -> Result<Json<u64>> {
    let query = ListQueryBuilder::new(&state.client);

    Ok(Json(query.count_object_groups().await?))
}

/// Params for a list s3 objects request.
#[derive(Debug, Deserialize)]
pub struct ListS3ObjectsParams {}

/// The list s3 objects handler.
pub async fn list_s3_objects(state: State<AppState>) -> Result<Json<Vec<S3Object>>> {
    let query = ListQueryBuilder::new(&state.client);

    Ok(Json(query.list_s3_objects().await?))
}

/// The count s3 objects handler.
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
    use crate::database::entities::object_group::Model as ObjectGroup;
    use crate::database::entities::s3_object::Model as S3Object;
    use crate::database::Client;
    use crate::queries::tests::initialize_database;
    use crate::routes::query_router;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_object_groups_api(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = initialize_database(&client, 10).await;

        let app = query_router(client);
        let response = app
            .oneshot(
                Request::builder()
                    .uri("/object_groups")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        let result = from_slice::<Vec<ObjectGroup>>(
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
        let client = Client::from_pool(pool);
        let entries = initialize_database(&client, 10).await;

        let app = query_router(client);
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
    async fn count_object_groups_api(pool: PgPool) {
        let client = Client::from_pool(pool);
        initialize_database(&client, 10).await;

        let app = query_router(client);
        let response = app
            .oneshot(
                Request::builder()
                    .uri("/object_groups/count")
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
        let client = Client::from_pool(pool);
        initialize_database(&client, 10).await;

        let app = query_router(client);
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
