//! OpenApi related models and code.
//!

use chrono::{DateTime, FixedOffset};
use serde_json::Value;
use utoipa::openapi::security::{Http, HttpAuthScheme, SecurityScheme};
use utoipa::{openapi, Modify, OpenApi, ToSchema};
use utoipa_swagger_ui::SwaggerUi;

use crate::database::entities::s3_object::Model as S3;
use crate::database::entities::sea_orm_active_enums::EventType;
use crate::database::entities::sea_orm_active_enums::StorageClass;
use crate::routes::error::ErrorResponse;
use crate::routes::filter::wildcard::Wildcard;
use crate::routes::get::*;
use crate::routes::ingest::*;
use crate::routes::list::*;
use crate::routes::pagination::*;
use crate::routes::presign::ContentDisposition;
use crate::routes::update::*;

/// A newtype equivalent to a `DateTime` with a time zone.
#[derive(ToSchema)]
#[schema(value_type = DateTime)]
pub struct DateTimeWithTimeZone(pub DateTime<FixedOffset>);

/// A newtype equivalent to an arbitrary JSON `Value`.
#[derive(ToSchema)]
#[schema(value_type = Value)]
pub struct Json(pub Value);

/// API docs.
#[derive(Debug, OpenApi)]
#[openapi(
    paths(
        list_s3,
        presign_s3,
        get_s3_by_id,
        presign_s3_by_id,
        count_s3,
        ingest_from_sqs,
        update_s3_attributes,
        update_s3_collection_attributes,
    ),
    components(
        schemas(
            S3,
            StorageClass,
            EventType,
            ErrorResponse,
            ListCount,
            IngestCount,
            DateTimeWithTimeZone,
            Wildcard,
            Json,
            ListResponseS3,
            ListResponseUrl,
            ContentDisposition,
            PaginatedResponse,
            Pagination,
            Links,
            PatchBody,
            Patch,
        )
    ),
    modifiers(&SecurityAddon),
    security(("orcabus_api_token" = []))
)]
pub struct ApiDoc;

/// Security add on for the API docs.
#[derive(Debug)]
pub struct SecurityAddon;

impl Modify for SecurityAddon {
    fn modify(&self, openapi: &mut openapi::OpenApi) {
        if let Some(components) = openapi.components.as_mut() {
            components.add_security_scheme(
                "orcabus_api_token",
                SecurityScheme::Http(Http::new(HttpAuthScheme::Bearer)),
            )
        }
    }
}

/// Create the swagger ui endpoint.
pub fn swagger_ui() -> SwaggerUi {
    SwaggerUi::new("/swagger-ui").url("/schema/openapi.json", ApiDoc::openapi())
}

#[cfg(test)]
mod tests {
    use aws_lambda_events::http::Request;
    use axum::body::Body;
    use axum::http::StatusCode;
    use sqlx::PgPool;
    use tower::ServiceExt;

    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::routes::router;
    use crate::routes::AppState;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn get_swagger_ui(pool: PgPool) {
        let app = router(AppState::from_pool(pool).await);
        let response = app
            .oneshot(
                Request::builder()
                    .uri("/swagger-ui")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::SEE_OTHER);
    }
}
