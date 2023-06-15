use std::net::{Ipv4Addr, SocketAddr};

use axum::{routing, Router, Server};
use hyper::Error;
use rust_api::file;
use utoipa::{
    openapi::security::{ApiKey, ApiKeyValue, SecurityScheme},
    Modify, OpenApi,
};
use utoipa_swagger_ui::SwaggerUi;

use tower_http::trace::{self, TraceLayer};
use tracing::{ info, Level };
//use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[tokio::main]
async fn main() -> Result<(), Error> {
    tracing_subscriber::fmt()
        .with_target(false)
        .compact()
        //.json()
        .init();

    // // TRACE
    // tracing_subscriber::registry()
    //     .with(tracing_subscriber::fmt::layer())
    //     .init();

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
    struct ApiDoc;

    #[derive(Clone)]
    struct AppState {}
    struct SecurityAddon;

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

    let db_result = rust_api::db::query().await;
    dbg!(&db_result);

    let app = Router::new()
        .merge(SwaggerUi::new("/swagger-ui").url("/api-docs/filemanager.json", ApiDoc::openapi()))
        .route("/file/", routing::get(file::search))
        .layer(
            TraceLayer::new_for_http()
                .make_span_with(trace::DefaultMakeSpan::new().level(Level::INFO))
                .on_response(trace::DefaultOnResponse::new().level(Level::INFO)),
        );

    let address = SocketAddr::from((Ipv4Addr::UNSPECIFIED, 8080));
    info!("listening on {}", address);
    Server::bind(&address).serve(app.into_make_service()).await
}
