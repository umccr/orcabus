//! OpenApi related models and code.
//!

use chrono::{DateTime, FixedOffset};
use serde_json::Value;
use utoipa::openapi::security::{Http, HttpAuthScheme, SecurityScheme};
use utoipa::{openapi, Modify, OpenApi, ToSchema};
use utoipa_swagger_ui::SwaggerUi;

use crate::database::entities::object::Model as FileObject;
use crate::database::entities::s3_object::Model as FileS3Object;
use crate::database::entities::sea_orm_active_enums::EventType;
use crate::database::entities::sea_orm_active_enums::StorageClass;
use crate::routes::attributes::*;
use crate::routes::get::*;
use crate::routes::ingest::*;
use crate::routes::list::*;
use crate::routes::ErrorResponse;

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
        list_objects,
        get_object_by_id,
        count_objects,
        list_s3_objects,
        get_s3_object_by_id,
        count_s3_objects,
        ingest_from_sqs,
    ),
    components(
        schemas(
            FileS3Object,
            FileObject,
            StorageClass,
            EventType,
            ErrorResponse,
            ListCount,
            IngestCount,
            DateTimeWithTimeZone,
            Json,
            ListResponseObject,
            ListResponseS3Object,
            MergeStrategy,
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
    SwaggerUi::new("/swagger_ui").url("/api_docs/openapi.json", ApiDoc::openapi())
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
        let app = router(AppState::from_pool(pool));
        let response = app
            .oneshot(
                Request::builder()
                    .uri("/swagger_ui")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::SEE_OTHER);
    }
}
