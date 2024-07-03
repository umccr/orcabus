use axum::serve;
use filemanager::database::Client;
use filemanager::env::Config;
use filemanager::error::Error::IoError;
use filemanager::error::Result;
use filemanager::handlers::init_tracing_with_format;
use filemanager::handlers::Format::Pretty;
use filemanager::routes::{router, AppState};
use http::Uri;
use std::io;
use std::sync::Arc;
use tokio::net::TcpListener;
use tracing::{debug, info};

#[tokio::main]
async fn main() -> Result<()> {
    let _ = dotenvy::dotenv();

    init_tracing_with_format(Pretty);

    let config = Arc::new(Config::load()?);
    debug!(?config, "running with config");

    let client = Client::from_config(&config).await?;
    let state = AppState::new(client, config.clone());

    let app = router(state);
    let listener = TcpListener::bind(config.api_server_addr().unwrap_or("localhost:8080")).await?;

    let local_addr = listener.local_addr()?;
    debug!("listening on {}", listener.local_addr()?);

    let docs = Uri::builder()
        .scheme("http")
        .authority(local_addr.to_string())
        .path_and_query("/swagger_ui")
        .build()
        .map_err(|err| IoError(io::Error::other(err)))?;

    info!("OpenAPI docs at {}", docs);

    Ok(serve(listener, app).await?)
}
