//! Route logic for get API calls.
//!

use axum::extract::{Path, State};
use axum::routing::get;
use axum::{Json, Router};
use uuid::Uuid;

use crate::database::entities::s3_object::Model as S3;
use crate::error::Error::ExpectedSomeValue;
use crate::error::Result;
use crate::queries::get::GetQueryBuilder;
use crate::routes::error::ErrorStatusCode;
use crate::routes::AppState;

/// Get an s3_object given it's id.
#[utoipa::path(
    get,
    path = "/s3_objects/{id}",
    responses(
        (status = OK, description = "The s3_object for the given id", body = S3),
        ErrorStatusCode,
    ),
    context_path = "/api/v1",
    tag = "get",
)]
pub async fn get_s3_by_id(state: State<AppState>, Path(id): Path<Uuid>) -> Result<Json<S3>> {
    let query = GetQueryBuilder::new(&state.client);

    Ok(Json(
        query
            .get_s3_by_id(id)
            .await?
            .ok_or_else(|| ExpectedSomeValue(id))?,
    ))
}

/// The router for getting object records.
pub fn get_router() -> Router<AppState> {
    Router::new().route("/s3_objects/:id", get(get_s3_by_id))
}

#[cfg(test)]
mod tests {
    use axum::body::Body;
    use axum::http::{Method, StatusCode};
    use sqlx::PgPool;

    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::queries::EntriesBuilder;
    use crate::routes::list::tests::{response_from, response_from_get};
    use crate::routes::AppState;
    use crate::uuid::UuidGenerator;
    use serde_json::Value;

    use super::*;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn get_s3_api(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = EntriesBuilder::default()
            .build(state.client())
            .await
            .s3_objects;

        let first = entries.first().unwrap();
        let result: S3 =
            response_from_get(state, &format!("/s3_objects/{}", first.s3_object_id)).await;
        assert_eq!(&result, first);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn get_non_existent(pool: PgPool) {
        let state = AppState::from_pool(pool);

        let (status_code, _) = response_from::<Value>(
            state,
            &format!("/s3_objects/{}", UuidGenerator::generate()),
            Method::GET,
            Body::empty(),
        )
        .await;
        assert_eq!(status_code, StatusCode::NOT_FOUND);
    }
}
