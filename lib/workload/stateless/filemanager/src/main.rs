use std::net::{Ipv4Addr, SocketAddr};

use axum::{routing, Router, Server};
use hyper::Error;

use filemanager::env;
use filemanager::file;
use filemanager::security::ApiDoc;

use utoipa::OpenApi;
use utoipa_swagger_ui::SwaggerUi;

use filemanager::events::SQSClient;
use tower_http::trace::{self, TraceLayer};
use tracing::{info, Level};

/// FileManager keeps track of files from many storage backend. The FileManager is responsible for:
///
/// 1. Listening and ingesting file creation events from the different storage backends.
/// 2. Querying on file attributes such as name, type of file, creation date, etc...
/// 3. Interfacing with htsget-rs for the biological-specific file formats: CRAM, BAM, VCF, BCF...
/// 4. Interacting with the metadata microservice to enrich the results of any particular query, returning
///    its associated metadata. A file should have a metadata id.
/// 5. Making sure the workflow run id is present and associated with any given file.
/// 6. Audit: Keep records for deleted objects even after the actual data is deleted.
/// 7. Audit: Record file ownership (on create, no chain of custody functionality needed).
///
/// All files have an external, public, file UUID so that they can be uniquely identified in our whole
/// microservices environment.

#[tokio::main]
async fn main() -> Result<(), Error> {
    tracing_subscriber::fmt()
        .with_target(false)
        .compact()
        .init();

    // prod or dev
    env::load_env();

    // let db_result = filemanager::db::s3_query_something("Marko".to_string()).await;
    // dbg!(&db_result);


    let sqs_client = SQSClient::with_default_client().await.unwrap();
    sqs_client.receive().await.unwrap();


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
