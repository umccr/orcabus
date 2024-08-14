//! Route logic for get API calls.
//!

use axum::extract::{Path, State};
use axum::routing::get;
use axum::{Json, Router};
use url::Url;
use uuid::Uuid;

use crate::database::entities::s3_object::Model as S3;
use crate::error::Error::ExpectedSomeValue;
use crate::error::Result;
use crate::queries::get::GetQueryBuilder;
use crate::routes::error::ErrorStatusCode;
use crate::routes::presign::PresignedUrlBuilder;
use crate::routes::AppState;

/// Get an s3_object given it's id.
#[utoipa::path(
    get,
    path = "/s3/{id}",
    responses(
        (status = OK, description = "The s3_object for the given id", body = S3),
        ErrorStatusCode,
    ),
    context_path = "/api/v1",
    tag = "get",
)]
pub async fn get_s3_by_id(state: State<AppState>, Path(id): Path<Uuid>) -> Result<Json<S3>> {
    let query = GetQueryBuilder::new(&state.database_client);

    Ok(Json(
        query
            .get_s3_by_id(id)
            .await?
            .ok_or_else(|| ExpectedSomeValue(id))?,
    ))
}

/// Generate AWS presigned URLs for a single S3 object using its `s3_object_id`.
/// This route will not return an object if it has been deleted from the database, or its size
/// is greater than `FILEMANAGER_API_PRESIGN_LIMIT`.
#[utoipa::path(
    get,
    path = "/s3/presign/{id}",
    responses(
        (status = OK, description = "The presigned url for the object with the id", body = Option<Url>),
        ErrorStatusCode,
    ),
    context_path = "/api/v1",
    tag = "get",
)]
pub async fn presign_s3_by_id(state: State<AppState>, id: Path<Uuid>) -> Result<Json<Option<Url>>> {
    let Json(response) = get_s3_by_id(state.clone(), id).await?;

    Ok(Json(
        PresignedUrlBuilder::presign_from_model(&state, response).await?,
    ))
}

/// The router for getting object records.
pub fn get_router() -> Router<AppState> {
    Router::new()
        .route("/s3/:id", get(get_s3_by_id))
        .route("/s3/presign/:id", get(presign_s3_by_id))
}

#[cfg(test)]
mod tests {
    use aws_smithy_mocks_experimental::{mock_client, RuleMode};
    use axum::body::Body;
    use axum::http::{Method, StatusCode};
    use sqlx::PgPool;

    use super::*;
    use crate::clients::aws::s3;
    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::env::Config;
    use crate::queries::EntriesBuilder;
    use crate::routes::list::tests::mock_get_object;
    use crate::routes::list::tests::{response_from, response_from_get};
    use crate::routes::AppState;
    use crate::uuid::UuidGenerator;
    use serde_json::Value;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn get_s3_api(pool: PgPool) {
        let state = AppState::from_pool(pool).await;
        let entries = EntriesBuilder::default()
            .build(state.database_client())
            .await
            .s3_objects;

        let first = entries.first().unwrap();
        let result: S3 = response_from_get(state, &format!("/s3/{}", first.s3_object_id)).await;
        assert_eq!(&result, first);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn get_non_existent(pool: PgPool) {
        let state = AppState::from_pool(pool).await;

        let (status_code, _) = response_from::<Value>(
            state,
            &format!("/s3/{}", UuidGenerator::generate()),
            Method::GET,
            Body::empty(),
        )
        .await;
        assert_eq!(status_code, StatusCode::NOT_FOUND);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn get_presign(pool: PgPool) {
        let client = mock_client!(
            aws_sdk_s3,
            RuleMode::Sequential,
            &[&mock_get_object("0", "0", b""),]
        );

        let state = AppState::from_pool(pool)
            .await
            .with_s3_client(s3::Client::new(client));

        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await;

        let result: Option<Url> = response_from_get(
            state,
            &format!("/s3/presign/{}", entries.s3_objects[0].s3_object_id),
        )
        .await;
        assert_eq!(result.unwrap().path(), "/0/0");
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn get_presign_different_count(pool: PgPool) {
        let client = mock_client!(
            aws_sdk_s3,
            RuleMode::Sequential,
            &[&mock_get_object("2", "2", b""),]
        );

        let config = Config {
            api_presign_limit: Some(1),
            ..Default::default()
        };
        let state = AppState::from_pool(pool)
            .await
            .with_config(config)
            .with_s3_client(s3::Client::new(client));

        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await;

        let result: Option<Url> = response_from_get(
            state,
            &format!("/s3/presign/{}", entries.s3_objects[2].s3_object_id),
        )
        .await;
        println!("{:#?}", result);
        assert!(result.is_none());
    }
}
