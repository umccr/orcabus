//! This module handles API routing.
//!

use std::sync::Arc;

use axum::Router;
use sqlx::PgPool;
use tower_http::trace::TraceLayer;

use crate::database::Client;
use crate::env::Config;
use crate::routes::error::fallback;
use crate::routes::get::*;
use crate::routes::ingest::ingest_router;
use crate::routes::list::*;
use crate::routes::openapi::swagger_ui;
use crate::routes::update::update_router;

pub mod error;
pub mod filtering;
pub mod get;
pub mod ingest;
pub mod list;
pub mod openapi;
pub mod pagination;
pub mod update;

/// App state containing database client.
#[derive(Debug, Clone)]
pub struct AppState {
    client: Client,
    config: Arc<Config>,
}

impl AppState {
    /// Create new state.
    pub fn new(client: Client, config: Arc<Config>) -> Self {
        Self { client, config }
    }

    /// Create a new state from an existing pool with default config.
    pub fn from_pool(pool: PgPool) -> Self {
        Self::new(Client::from_pool(pool), Default::default())
    }

    /// Get the client.
    pub fn client(&self) -> &Client {
        &self.client
    }

    /// Get the config.
    pub fn config(&self) -> &Arc<Config> {
        &self.config
    }
}

/// Prefixed router with a version number, swagger ui and fallback route.
pub fn router(state: AppState) -> Router {
    Router::new()
        .nest("/api/v1", api_router(state))
        .fallback(fallback)
        .merge(swagger_ui())
}

/// The main filemanager router for requests.
pub fn api_router(state: AppState) -> Router {
    Router::new()
        .merge(get_router())
        .merge(ingest_router())
        .merge(list_router())
        .merge(update_router())
        .with_state(state)
        .layer(TraceLayer::new_for_http())
}

#[cfg(test)]
mod tests {
    use aws_lambda_events::http::Request;
    use axum::body::Body;
    use axum::http::StatusCode;
    use axum::response::IntoResponse;
    use sqlx::PgPool;
    use tower::ServiceExt;

    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::error::Error;
    use crate::routes::{router, AppState};

    #[tokio::test]
    async fn internal_error_into_response() {
        let response = Error::MigrateError("error".to_string()).into_response();
        assert_eq!(response.status(), StatusCode::INTERNAL_SERVER_ERROR);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn get_unknown_path(pool: PgPool) {
        let app = router(AppState::from_pool(pool));
        let response = app
            .oneshot(
                Request::builder()
                    .uri("/not_found")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        assert_eq!(response.status(), StatusCode::NOT_FOUND);
    }
}
