use std::net::{Ipv4Addr, SocketAddr};

use axum::{routing, Router, Server};
use hyper::Error;

use rust_api::env;
use rust_api::file;
use rust_api::security::ApiDoc;

use utoipa::OpenApi;
use utoipa_swagger_ui::SwaggerUi;

use tower_http::trace::{self, TraceLayer};
use tracing::{ info, Level };

#[tokio::main]
async fn main() -> Result<(), Error> {
    tracing_subscriber::fmt()
        .with_target(false)
        .compact()
        .init();
    
    // prod or dev
    env::load_env();

    let db_result = rust_api::db::s3_query_something().await;
    dbg!(&db_result);

    let app = Router::new()
        // TODO: Have this swagger/openapi path enabled via (non-default?) feature flag
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
