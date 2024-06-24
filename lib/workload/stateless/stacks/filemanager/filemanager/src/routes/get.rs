//! Route logic for get API calls.
//!

use axum::extract::{Path, State};
use axum::Json;
use serde::Deserialize;
use uuid::Uuid;

use crate::database::entities::object_group::Model as ObjectGroup;
use crate::database::entities::s3_object::Model as S3Object;
use crate::error::Result;
use crate::queries::get::GetQueryBuilder;
use crate::routes::AppState;

/// Params for a get object group by id request.
#[derive(Debug, Deserialize)]
pub struct GetObjectGroupById {}

/// The get object groups handler.
pub async fn get_object_group_by_id(
    state: State<AppState>,
    Path(id): Path<Uuid>,
) -> Result<Json<Option<ObjectGroup>>> {
    let query = GetQueryBuilder::new(&state.client);

    Ok(Json(query.get_object_group(id).await?))
}

/// Params for a get s3 objects by id request.
#[derive(Debug, Deserialize)]
pub struct GetS3ObjectById {}

/// The get s3 objects handler.
pub async fn get_s3_object_by_id(
    state: State<AppState>,
    Path(id): Path<Uuid>,
) -> Result<Json<Option<S3Object>>> {
    let query = GetQueryBuilder::new(&state.client);

    Ok(Json(query.get_s3_object_by_id(id).await?))
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
    async fn get_object_groups_api(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = initialize_database(&client, 10).await;

        let first = entries.first().unwrap();
        let app = query_router(client);
        let response = app
            .oneshot(
                Request::builder()
                    .uri(format!("/object_groups/{}", first.0.object_id))
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        let result = from_slice::<ObjectGroup>(
            to_bytes(response.into_body(), usize::MAX)
                .await
                .unwrap()
                .as_bytes(),
        )
        .unwrap();

        assert_eq!(result, first.0);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn get_s3_objects_api(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = initialize_database(&client, 10).await;

        let first = entries.first().unwrap();
        let app = query_router(client);
        let response = app
            .oneshot(
                Request::builder()
                    .uri(format!("/s3_objects/{}", first.1.s3_object_id))
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        let result = from_slice::<S3Object>(
            to_bytes(response.into_body(), usize::MAX)
                .await
                .unwrap()
                .as_bytes(),
        )
        .unwrap();

        assert_eq!(result, first.1);
    }
}
