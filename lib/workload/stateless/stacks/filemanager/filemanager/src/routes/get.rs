//! Route logic for get API calls.
//!

use axum::extract::{Request, State};
use axum::http::header::{CONTENT_ENCODING, CONTENT_TYPE};
use axum::routing::get;
use axum::{extract, Json, Router};
use axum_extra::extract::WithRejection;
use sea_orm::{ConnectionTrait, TransactionTrait};
use url::Url;
use uuid::Uuid;

use crate::database::entities::s3_object;
use crate::database::entities::s3_object::Model as S3;
use crate::error::Error::ExpectedSomeValue;
use crate::error::Result;
use crate::queries::get::GetQueryBuilder;
use crate::queries::list::ListQueryBuilder;
use crate::routes::error::{ErrorStatusCode, Path, Query};
use crate::routes::filter::wildcard::Wildcard;
use crate::routes::filter::S3ObjectsFilter;
use crate::routes::header::HeaderParser;
use crate::routes::presign::{PresignedParams, PresignedUrlBuilder};
use crate::routes::AppState;

async fn get_s3_from_connection<C>(
    connection: &C,
    WithRejection(extract::Path(id), _): Path<Uuid>,
) -> Result<Json<S3>>
where
    C: ConnectionTrait,
{
    let query = GetQueryBuilder::new(connection);

    Ok(Json(
        query
            .get_s3_by_id(id)
            .await?
            .ok_or_else(|| ExpectedSomeValue(id))?,
    ))
}

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
pub async fn get_s3_by_id(state: State<AppState>, id: Path<Uuid>) -> Result<Json<S3>> {
    get_s3_from_connection(state.database_client().connection_ref(), id).await
}

/// Implementation of presigning a single URL by id.
async fn presign_url_by_id(
    state: State<AppState>,
    id: Path<Uuid>,
    presigned: Query<PresignedParams>,
    request: Request,
    access_key_secret_id: Option<String>,
) -> Result<Json<Option<Url>>> {
    let txn = state.database_client().connection_ref().begin().await?;

    let Json(response) = get_s3_from_connection(&txn, id).await?;

    // If this object is not current or it's not accessible because it's archived, return an
    // empty response.
    if !response.is_current_state || !response.is_accessible {
        txn.commit().await?;
        return Ok(Json(None));
    }

    // Check if this represents a current object.
    let current = ListQueryBuilder::<_, s3_object::Entity>::new(&txn)
        .filter_all(
            S3ObjectsFilter {
                bucket: vec![Wildcard::new(response.bucket.to_string())].into(),
                key: vec![Wildcard::new(response.key.to_string())].into(),
                version_id: vec![Wildcard::new(response.version_id.to_string())].into(),
                ..Default::default()
            },
            true,
            true,
        )?
        .all()
        .await?;

    txn.commit().await?;

    let content_type = HeaderParser::new(request.headers()).parse_header(CONTENT_TYPE)?;
    let content_encoding = HeaderParser::new(request.headers()).parse_header(CONTENT_ENCODING)?;

    // If the last object ordered by sequencer is the requested one, then this is a
    // current object.
    if let Some(current) = current.last() {
        if current.s3_object_id == response.s3_object_id {
            return Ok(Json(
                PresignedUrlBuilder::presign_from_model(
                    &state,
                    response,
                    presigned.response_content_disposition(),
                    content_type,
                    content_encoding,
                    access_key_secret_id.as_deref(),
                )
                .await?,
            ));
        }
    }

    Ok(Json(None))
}

/// Generate AWS presigned URLs for a single S3 object using its `s3_object_id`.
/// This route will not return an object if it is not a current record, or it's storage class is
/// not accessible because it is archived, or its size is greater than
/// `FILEMANAGER_API_PRESIGN_LIMIT`. Presigned URLs live for up to 7 days.
#[utoipa::path(
    get,
    path = "/s3/presign/{id}",
    responses(
        (status = OK, description = "The presigned url for the object with the id", body = Option<Url>),
        ErrorStatusCode,
    ),
    params(PresignedParams),
    context_path = "/api/v1",
    tag = "get",
)]
pub async fn presign_s3_by_id(
    state: State<AppState>,
    id: Path<Uuid>,
    presigned: Query<PresignedParams>,
    request: Request,
) -> Result<Json<Option<Url>>> {
    let access_key_secret_id = state
        .config()
        .access_key_secret_id()
        .map(|secret| secret.to_string());
    // Always presign with access key if it's available.
    presign_url_by_id(state, id, presigned, request, access_key_secret_id).await
}

/// The router for getting object records.
pub fn get_router() -> Router<AppState> {
    Router::new()
        .route("/s3/{id}", get(get_s3_by_id))
        .route("/s3/presign/{id}", get(presign_s3_by_id))
}

#[cfg(test)]
mod tests {
    use aws_smithy_mocks_experimental::{mock_client, RuleMode};
    use axum::body::Body;
    use axum::http::{Method, StatusCode};
    use serde_json::Value;
    use sqlx::PgPool;

    use crate::clients::aws::s3;
    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::env::Config;
    use crate::queries::EntriesBuilder;
    use crate::routes::list::tests::mock_get_object;
    use crate::routes::list::tests::{response_from, response_from_get};
    use crate::routes::presign::tests::assert_presigned_params;
    use crate::routes::AppState;
    use crate::uuid::UuidGenerator;

    use super::*;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn get_s3_api(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let entries = EntriesBuilder::default()
            .build(state.database_client())
            .await
            .unwrap()
            .s3_objects;

        let first = entries.first().unwrap();
        let result: S3 = response_from_get(state, &format!("/s3/{}", first.s3_object_id)).await;
        assert_eq!(&result, first);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn get_non_existent(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();

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
            &[&mock_get_object("2", "1", b""),]
        );

        let state = AppState::from_pool(pool)
            .await
            .unwrap()
            .with_s3_client(s3::Client::new(client));

        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap();

        let result = response_from_get::<Option<Url>>(
            state.clone(),
            &format!("/s3/presign/{}", entries.s3_objects[2].s3_object_id),
        )
        .await
        .unwrap();

        let query = result.query().unwrap();
        assert_presigned_params(query, "inline");
        assert_eq!(result.path(), "/1/2");

        // Not accessible because of storage class.
        let result = response_from_get::<Option<Url>>(
            state,
            &format!("/s3/presign/{}", entries.s3_objects[0].s3_object_id),
        )
        .await;
        assert!(result.is_none());
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn get_presign_attachment(pool: PgPool) {
        let client = mock_client!(
            aws_sdk_s3,
            RuleMode::Sequential,
            &[&mock_get_object("2", "1", b""),]
        );

        let state = AppState::from_pool(pool)
            .await
            .unwrap()
            .with_s3_client(s3::Client::new(client));

        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap();

        let result = response_from_get::<Option<Url>>(
            state,
            &format!(
                "/s3/presign/{}?responseContentDisposition=attachment",
                entries.s3_objects[2].s3_object_id
            ),
        )
        .await
        .unwrap();

        let query = result.query().unwrap();
        assert_presigned_params(query, "attachment%3B%20filename%3D%222%22");
        assert_eq!(result.path(), "/1/2");
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn get_presign_different_size(pool: PgPool) {
        let client = mock_client!(
            aws_sdk_s3,
            RuleMode::Sequential,
            &[&mock_get_object("1", "2", b""),]
        );

        let config = Config {
            api_presign_limit: Some(1),
            ..Default::default()
        };
        let state = AppState::from_pool(pool)
            .await
            .unwrap()
            .with_config(config)
            .with_s3_client(s3::Client::new(client));

        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap();

        let result: Option<Url> = response_from_get(
            state,
            &format!("/s3/presign/{}", entries.s3_objects[2].s3_object_id),
        )
        .await;
        assert!(result.is_none());
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn get_presign_not_current_deleted(pool: PgPool) {
        let client = mock_client!(
            aws_sdk_s3,
            RuleMode::Sequential,
            &[&mock_get_object("3", "1", b""),]
        );

        let state = AppState::from_pool(pool)
            .await
            .unwrap()
            .with_s3_client(s3::Client::new(client));

        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap();

        let result: Option<Url> = response_from_get(
            state,
            &format!("/s3/presign/{}", entries.s3_objects[3].s3_object_id),
        )
        .await;
        assert!(result.is_none());
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn get_presign_not_current_created(pool: PgPool) {
        let client = mock_client!(
            aws_sdk_s3,
            RuleMode::Sequential,
            &[&mock_get_object("0", "0", b""),]
        );

        let state = AppState::from_pool(pool)
            .await
            .unwrap()
            .with_s3_client(s3::Client::new(client));

        let entries = EntriesBuilder::default()
            .with_bucket_divisor(4)
            .with_key_divisor(3)
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap();

        let result: Option<Url> = response_from_get(
            state,
            &format!("/s3/presign/{}", entries.s3_objects[0].s3_object_id),
        )
        .await;
        assert!(result.is_none());
    }
}
