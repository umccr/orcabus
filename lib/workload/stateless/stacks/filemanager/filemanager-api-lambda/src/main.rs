use std::sync::Arc;

use axum::extract::{Request, State};
use axum::middleware::{from_fn_with_state, Next};
use axum::response::{IntoResponse, Response};
use lambda_http::run;
use lambda_http::Error;
use tracing::debug;

use filemanager::clients::aws::{s3, secrets_manager, sqs};
use filemanager::database::Client;
use filemanager::env::Config;
use filemanager::handlers::aws::{create_database_pool, update_credentials};
use filemanager::handlers::init_tracing;
use filemanager::routes::error::{ErrorResponse, ErrorStatusCode};
use filemanager::routes::{router, AppState};

#[tokio::main]
async fn main() -> Result<(), Error> {
    init_tracing();

    let config = Config::load()?;
    debug!(?config, "running with config");

    let client = Client::new(create_database_pool(&config).await?);
    let state = AppState::new(
        client,
        Arc::new(config),
        Arc::new(s3::Client::with_defaults().await),
        Arc::new(sqs::Client::with_defaults().await),
        Arc::new(secrets_manager::Client::with_defaults().await?),
        // API Gateway is always TLS.
        true,
    );

    let app = router(state.clone())?
        .route_layer(from_fn_with_state(state, update_credentials_middleware));

    run(app).await
}

/// Update credentials when processing a request.
async fn update_credentials_middleware(
    State(state): State<AppState>,
    request: Request,
    next: Next,
) -> Response {
    let result = update_credentials(state.database_client().connection_ref(), state.config()).await;

    if let Err(err) = result {
        return ErrorStatusCode::InternalServerError(ErrorResponse::new(format!(
            "failed to update credentials: {}",
            err
        )))
        .into_response();
    }

    next.run(request).await
}
