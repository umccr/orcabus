use axum::extract::{Request, State};
use axum::middleware::{from_fn_with_state, Next};
use axum::response::{IntoResponse, Response};
use filemanager::env::Config;
use lambda_http::Error;
use std::sync::Arc;

use filemanager::database::Client;
use filemanager::handlers::aws::{create_database_pool, update_credentials};
use filemanager::handlers::init_tracing;
use filemanager::routes::{api_router, AppState, ErrorResponse, ErrorStatusCode};
use lambda_http::run;
use tracing::debug;

#[tokio::main]
async fn main() -> Result<(), Error> {
    init_tracing();

    let config = Config::load()?;
    debug!(?config, "running with config");

    let client = Client::new(create_database_pool(&config).await?);
    let state = AppState::new(client, Arc::new(config));

    let app = api_router(state.clone())
        .route_layer(from_fn_with_state(state, update_credentials_middleware));

    run(app).await
}

/// Update credentials when processing a request.
async fn update_credentials_middleware(
    State(state): State<AppState>,
    request: Request,
    next: Next,
) -> Response {
    let result = update_credentials(state.client().connection_ref(), state.config()).await;

    if let Err(err) = result {
        return ErrorStatusCode::RequestTimeout(ErrorResponse::new(format!(
            "failed to update credentials: {}",
            err
        )))
        .into_response();
    }

    next.run(request).await
}
