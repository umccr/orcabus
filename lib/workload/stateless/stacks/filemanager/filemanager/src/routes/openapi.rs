//! OpenApi related models and code.
//!

use crate::database::entities::sea_orm_active_enums::CrawlStatus;
use crate::routes::crawl::CrawlRequest;
use chrono::{DateTime, FixedOffset};
use serde_json::Value;
use utoipa::openapi::security::{Http, HttpAuthScheme, SecurityScheme};
use utoipa::{openapi, Modify, OpenApi, ToSchema};
use utoipa_swagger_ui::SwaggerUi;

use crate::database::entities::s3_crawl::Model as Crawl;
use crate::database::entities::s3_object::Model as S3;
use crate::database::entities::sea_orm_active_enums::ArchiveStatus;
use crate::database::entities::sea_orm_active_enums::EventType;
use crate::database::entities::sea_orm_active_enums::Reason;
use crate::database::entities::sea_orm_active_enums::StorageClass;
use crate::routes::crawl::*;
use crate::routes::error::ErrorResponse;
use crate::routes::filter::wildcard::Wildcard;
use crate::routes::filter::*;
use crate::routes::get::*;
use crate::routes::ingest::*;
use crate::routes::list::*;
use crate::routes::pagination::*;
use crate::routes::presign::ContentDisposition;
use crate::routes::update::*;

/// The path to the swagger ui.
pub const SWAGGER_UI_PATH: &str = "/schema/swagger-ui";

/// A newtype equivalent to a `DateTime` with a time zone.
#[derive(ToSchema)]
#[schema(value_type = DateTime, format = DateTime)]
pub struct DateTimeWithTimeZone(pub DateTime<FixedOffset>);

/// A newtype equivalent to an arbitrary JSON `Value`.
#[derive(ToSchema)]
#[schema(value_type = Value)]
pub struct Json(pub Value);

/// A newtype equivalent to a `url::Url`.
#[derive(ToSchema)]
#[schema(value_type = Url)]
pub struct Url(pub url::Url);

/// A newtype equivalent to a `uuid::Uuid`.
#[derive(ToSchema)]
#[schema(value_type = Uuid)]
pub struct Uuid(pub uuid::Uuid);

/// API docs.
#[derive(Debug, OpenApi)]
#[openapi(
    paths(
        list_s3,
        presign_s3,
        attributes_s3,
        get_s3_by_id,
        presign_s3_by_id,
        count_s3,
        ingest_from_sqs,
        update_s3_attributes,
        update_s3_collection_attributes,
        crawl_s3,
        crawl_sync_s3,
        list_crawl_s3,
        count_crawl_s3,
        get_crawl_s3_by_id
    ),
    components(
        schemas(
            S3,
            StorageClass,
            ArchiveStatus,
            Reason,
            EventType,
            ErrorResponse,
            ListCount,
            IngestCount,
            DateTimeWithTimeZone,
            Wildcard,
            Json,
            ListResponse<Url>,
            ListResponse<S3>,
            ContentDisposition,
            PaginatedResponse,
            Pagination,
            Links,
            PatchBody,
            Patch,
            Join,
            FilterJoin<Wildcard>,
            FilterJoin<StorageClass>,
            FilterJoin<i64>,
            FilterJoin<Uuid>,
            FilterJoin<Reason>,
            FilterJoin<ArchiveStatus>,
            FilterJoin<CrawlStatus>,
            Crawl,
            CrawlRequest
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
    SwaggerUi::new(SWAGGER_UI_PATH).url("/schema/openapi.json", ApiDoc::openapi())
}

#[cfg(test)]
mod tests {
    use aws_lambda_events::http::Request;
    use axum::body::Body;
    use axum::http::StatusCode;
    use sqlx::PgPool;
    use tower::util::ServiceExt;

    use super::*;
    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::routes::router;
    use crate::routes::AppState;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn get_swagger_ui(pool: PgPool) {
        let app = router(AppState::from_pool(pool).await.unwrap()).unwrap();
        let response = app
            .oneshot(
                Request::builder()
                    .uri(SWAGGER_UI_PATH)
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::SEE_OTHER);
    }
}
