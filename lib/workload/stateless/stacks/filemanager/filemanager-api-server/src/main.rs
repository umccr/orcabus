use axum::serve;
use filemanager::database::Client;
use filemanager::env::Config;
use filemanager::error::Result;
use filemanager::handlers::init_tracing_with_format;
use filemanager::handlers::Format::Pretty;
use filemanager::routes::{api_router, AppState};
use std::sync::Arc;
use tokio::net::TcpListener;
use tracing::debug;

#[tokio::main]
async fn main() -> Result<()> {
    let _ = dotenvy::dotenv();

    init_tracing_with_format(Pretty);

    let config = Arc::new(Config::load()?);
    debug!(?config, "running with config");

    let client = Client::from_config(&config).await?;
    let state = AppState::new(client, config.clone());

    let app = api_router(state);

    let listener = TcpListener::bind(config.api_server_addr()).await?;
    debug!("listening on {}", listener.local_addr()?);

    Ok(serve(listener, app).await?)
}
