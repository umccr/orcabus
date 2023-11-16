use std::net::{Ipv4Addr, SocketAddr};

use axum::{routing, Router, Server};

use rust_api::env;
use rust_api::file;
use rust_api::security::ApiDoc;

use utoipa::OpenApi;
use utoipa_swagger_ui::SwaggerUi;

use tower_http::trace::{self, TraceLayer};
use tracing::{info, Level};

/// FileManager keeps track of files from many storage backend. All files have an external, public, 
/// file UUID so that they can be uniquely identified in our whole microservices environment.
///
/// The FileManager is responsible for:
///
/// 1. Listening and ingesting (indexing) file creation events from the different storage backends.
/// 2. Querying on file attributes such as name, type of file, creation date, etc...
/// 3. Record file provenance (on create, on delete).
/// 4. Record object lifecycle status, i.e: Tier transition, backup to different storage, deletion.
/// 5. Manage object identity, i.e: UUID, path, etc...
/// 
/// Non goals:
/// 
/// 1. Perform checksumming of files: Too computationally expensive for our file sizes.
/// 2. Link objects/paths to metadata: That would tightly couple filemanager with metadata service.

#[tokio::main]
async fn main() -> Result<(), hyper::Error> {
    tracing_subscriber::fmt()
        .with_target(false)
        .compact()
        .init();

    // prod or dev
    env::load_env();

    let db_result = rust_api::db::s3_query_something("query".to_string()).await;
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
    let server = Server::bind(&address).serve(app.into_make_service());

    // Run forever-ish...
    if let Err(err) = server.await {
        eprintln!("server error: {}", err);
    }

    Ok(())
}
