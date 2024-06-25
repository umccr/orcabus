use axum::serve;
use filemanager::database::Client;
use filemanager::env::Config;
use filemanager::error::Result;
use filemanager::routes::query_router;
use tokio::net::TcpListener;
use tracing::debug;

#[tokio::main]
async fn main() -> Result<()> {
    let config = Config::load()?;
    let client = Client::from_config(&config).await?;

    let app = query_router(client);

    let listener = TcpListener::bind(config.api_server_addr().unwrap_or("localhost:8080")).await?;
    debug!("listening on {}", listener.local_addr()?);

    Ok(serve(listener, app).await?)
}
