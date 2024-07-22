//! Route logic for get API calls.
//!

use axum::extract::{Path, State};
use axum::Json;
use serde::Deserialize;
use uuid::Uuid;

use crate::database::entities::object::Model as FileObject;
use crate::database::entities::s3_object::Model as FileS3Object;
use crate::error::Result;
use crate::queries::get::GetQueryBuilder;
use crate::routes::{AppState, ErrorStatusCode};

/// Params for a get object by id request.
#[derive(Debug, Deserialize)]
pub struct GetObjectById {}

/// The get object handler.
#[utoipa::path(
    get,
    path = "/objects/{id}",
    responses(
        (status = OK, description = "Get an object by its object_id", body = Option<FileObject>),
        ErrorStatusCode,
    ),
    context_path = "/api/v1",
)]
pub async fn get_object_by_id(
    state: State<AppState>,
    Path(id): Path<Uuid>,
) -> Result<Json<Option<FileObject>>> {
    let query = GetQueryBuilder::new(&state.client);

    Ok(Json(query.get_object(id).await?))
}

/// Params for a get s3 objects by id request.
#[derive(Debug, Deserialize)]
pub struct GetS3ObjectById {}

/// The get s3 objects handler.
#[utoipa::path(
    get,
    path = "/s3_objects/{id}",
    responses(
        (status = OK, description = "Get an s3object by its s3_object_id", body = Option<FileS3Object>),
        ErrorStatusCode,
    ),
    context_path = "/api/v1",
)]
pub async fn get_s3_object_by_id(
    state: State<AppState>,
    Path(id): Path<Uuid>,
) -> Result<Json<Option<FileS3Object>>> {
    let query = GetQueryBuilder::new(&state.client);

    Ok(Json(query.get_s3_object_by_id(id).await?))
}

#[cfg(test)]
mod tests {
    use sqlx::PgPool;

    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::entities::object::Model as Object;
    use crate::database::entities::s3_object::Model as S3Object;
    use crate::queries::tests::initialize_database;
    use crate::routes::list::tests::response_from_get;
    use crate::routes::AppState;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn get_objects_api(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = initialize_database(state.client(), 10).await.objects;

        let first = entries.first().unwrap();
        let result: Object =
            response_from_get(state, &format!("/objects/{}", first.object_id)).await;
        assert_eq!(&result, first);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn get_s3_objects_api(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = initialize_database(state.client(), 10).await.s3_objects;

        let first = entries.first().unwrap();
        let result: S3Object =
            response_from_get(state, &format!("/s3_objects/{}", first.s3_object_id)).await;
        assert_eq!(&result, first);
    }
}
