//! This module handles API routing.
//!

use std::sync::Arc;

use crate::clients::aws::s3;
use crate::database;
use crate::env::Config;
use crate::routes::error::fallback;
use crate::routes::get::*;
use crate::routes::ingest::ingest_router;
use crate::routes::list::*;
use crate::routes::openapi::swagger_ui;
use crate::routes::update::update_router;
use axum::Router;
use sqlx::PgPool;
use tower_http::trace::TraceLayer;

pub mod error;
pub mod filter;
pub mod get;
pub mod ingest;
pub mod list;
pub mod openapi;
pub mod pagination;
pub mod presign;
pub mod update;

/// App state containing database client.
#[derive(Debug, Clone)]
pub struct AppState {
    database_client: database::Client,
    config: Arc<Config>,
    s3_client: Arc<s3::Client>,
    use_tls_links: bool,
}

impl AppState {
    /// Create new state.
    pub fn new(
        database_client: database::Client,
        config: Arc<Config>,
        s3_client: Arc<s3::Client>,
        use_tls_links: bool,
    ) -> Self {
        Self {
            database_client,
            config,
            s3_client,
            use_tls_links,
        }
    }

    /// Create a new state from an existing pool with default config.
    pub async fn from_pool(pool: PgPool) -> Self {
        Self::new(
            database::Client::from_pool(pool),
            Default::default(),
            Arc::new(s3::Client::with_defaults().await),
            false,
        )
    }

    /// Modify the config.
    pub fn with_config(mut self, config: Config) -> Self {
        self.config = Arc::new(config);
        self
    }

    /// Modify the database client.
    pub fn with_database_client(mut self, client: database::Client) -> Self {
        self.database_client = client;
        self
    }

    /// Modify the s3 client.
    pub fn with_s3_client(mut self, client: s3::Client) -> Self {
        self.s3_client = Arc::new(client);
        self
    }

    /// Set the TLS links option.
    pub fn with_use_tls_links(mut self, use_tls_links: bool) -> Self {
        self.use_tls_links = use_tls_links;
        self
    }

    /// Get the database client.
    pub fn database_client(&self) -> &database::Client {
        &self.database_client
    }

    /// Get the config.
    pub fn config(&self) -> &Config {
        &self.config
    }

    /// Get the database client.
    pub fn s3_client(&self) -> &s3::Client {
        &self.s3_client
    }

    /// Get the links TLS setting.
    pub fn use_tls_links(&self) -> bool {
        self.use_tls_links
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
        let app = router(AppState::from_pool(pool).await);
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
