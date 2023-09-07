use crate::file;

use utoipa::{
    openapi::security::{ApiKey, ApiKeyValue, SecurityScheme},
    Modify, OpenApi,
};

pub struct SecurityAddon;

impl Modify for SecurityAddon {
    fn modify(&self, openapi: &mut utoipa::openapi::OpenApi) {
        if let Some(components) = openapi.components.as_mut() {
            components.add_security_scheme(
                "api_key",
                SecurityScheme::ApiKey(ApiKey::Header(ApiKeyValue::new("File_apikey"))),
            )
        }
    }
}

#[derive(OpenApi)]
#[openapi(
    paths(
        file::search,
    ),
    components(
        schemas(file::File, file::FileError)
    ),
    modifiers(&SecurityAddon),
    tags(
        (name = "File", description = "File manager API")
    )
)]
pub struct ApiDoc;
