//! OpenApi related models and code.
//!

use crate::database::entities::object::Model as FileObject;
use crate::database::entities::s3_object::Model as FileS3Object;
use crate::database::entities::sea_orm_active_enums::EventType;
use crate::database::entities::sea_orm_active_enums::StorageClass;
use crate::routes::get::*;
use crate::routes::list::*;
use crate::routes::ErrorResponse;
use chrono::{DateTime, FixedOffset};
use serde_json::Value;
use utoipa::openapi::security::{Http, HttpAuthScheme, SecurityScheme};
use utoipa::{openapi, Modify, OpenApi, ToSchema};
use utoipa_swagger_ui::SwaggerUi;

/// A newtype representing a chrono DateTime used to link to the utoipa `DateTime` known value.
#[derive(ToSchema)]
#[schema(value_type = DateTime)]
pub struct DateTimeWithTimeZone(pub DateTime<FixedOffset>);

/// A newtype representing a json Value used to link to the utoipa `Value` known value.
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
    ),
    components(
        schemas(
            FileS3Object,
            FileObject,
            StorageClass,
            EventType,
            ErrorResponse,
            DateTimeWithTimeZone,
            Json,
        )
    ),
    modifiers(&SecurityAddon),
    security(("orcabus_api_key" = []))
)]
pub struct ApiDoc;

/// Security add on for the API docs.
#[derive(Debug)]
pub struct SecurityAddon;

impl Modify for SecurityAddon {
    fn modify(&self, openapi: &mut openapi::OpenApi) {
        if let Some(components) = openapi.components.as_mut() {
            components.add_security_scheme(
                "orcabus_api_key",
                SecurityScheme::Http(Http::new(HttpAuthScheme::Bearer)),
            )
        }
    }
}

/// Create the swagger ui endpoint.
pub fn swagger_ui() -> SwaggerUi {
    SwaggerUi::new("/swagger_ui").url("/api_docs/openapi.json", ApiDoc::openapi())
}
