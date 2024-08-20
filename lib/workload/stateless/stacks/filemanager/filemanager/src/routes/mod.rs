//! This module handles API routing.
//!

use crate::clients::aws::s3;
use crate::database;
use crate::env::Config;
use crate::error::Error::ApiConfigurationError;
use crate::error::Result;
use crate::routes::error::fallback;
use crate::routes::get::*;
use crate::routes::ingest::ingest_router;
use crate::routes::list::*;
use crate::routes::openapi::swagger_ui;
use crate::routes::update::update_router;
use axum::http::header::AUTHORIZATION;
use axum::http::{HeaderValue, Method};
use axum::Router;
use chrono::Duration;
use sqlx::PgPool;
use std::sync::Arc;
use tower_http::cors::CorsLayer;
use tower_http::trace::TraceLayer;
use tracing::trace;

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
pub fn router(state: AppState) -> Result<Router> {
    Ok(Router::new()
        .nest("/api/v1", api_router(state)?)
        .fallback(fallback)
        .merge(swagger_ui()))
}

/// Configure the cors layer
pub fn cors_layer(allow_origins: Option<&[String]>) -> Result<CorsLayer> {
    let mut layer = CorsLayer::new()
        .allow_headers([AUTHORIZATION])
        .allow_methods([
            Method::GET,
            Method::HEAD,
            Method::OPTIONS,
            Method::POST,
            Method::PATCH,
        ])
        .max_age(
            Duration::days(10)
                .to_std()
                .map_err(|err| ApiConfigurationError(err.to_string()))?,
        );

    if let Some(origins) = allow_origins {
        let origins = origins
            .iter()
            .map(|origin| {
                origin
                    .parse::<HeaderValue>()
                    .map_err(|err| ApiConfigurationError(err.to_string()))
            })
            .collect::<Result<Vec<_>>>()?;

        layer = layer.allow_origin(origins);
    }

    trace!(layer = ?layer, "cors");
    Ok(layer)
}

/// The main filemanager router for requests.
pub fn api_router(state: AppState) -> Result<Router> {
    Ok(Router::new()
        .merge(get_router())
        .merge(ingest_router())
        .merge(list_router())
        .merge(update_router())
        .layer(cors_layer(state.config().api_cors_allow_origins())?)
        .layer(TraceLayer::new_for_http())
        .with_state(state))
}

#[cfg(test)]
mod tests {
    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::env::Config;
    use crate::error::Error;
    use crate::routes::{router, AppState};
    use aws_lambda_events::http::header::ACCESS_CONTROL_ALLOW_HEADERS;
    use aws_lambda_events::http::Request;
    use axum::body::Body;
    use axum::http::header::{
        ACCESS_CONTROL_ALLOW_METHODS, ACCESS_CONTROL_ALLOW_ORIGIN, ACCESS_CONTROL_REQUEST_HEADERS,
        ACCESS_CONTROL_REQUEST_METHOD, HOST, ORIGIN,
    };
    use axum::http::{Method, StatusCode};
    use axum::response::IntoResponse;
    use sqlx::PgPool;
    use std::sync::Arc;
    use tower::ServiceExt;

    #[tokio::test]
    async fn internal_error_into_response() {
        let response = Error::MigrateError("error".to_string()).into_response();
        assert_eq!(response.status(), StatusCode::INTERNAL_SERVER_ERROR);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn get_unknown_path(pool: PgPool) {
        let app = router(AppState::from_pool(pool).await).unwrap();
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

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_cors(pool: PgPool) {
        let mut state = AppState::from_pool(pool).await;
        state.config = Arc::new(Config {
            api_cors_allow_origins: Some(vec![
                "localhost:8000".to_string(),
                "http://example.com".to_string(),
            ]),
            ..Default::default()
        });

        let app = router(state.clone()).unwrap();
        let response = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/s3")
                    .header(ORIGIN, "127.0.0.1")
                    .header(HOST, "127.0.0.1")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert!(response
            .headers()
            .get(ACCESS_CONTROL_ALLOW_ORIGIN)
            .is_none());

        let app = router(state.clone()).unwrap();
        let response = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/s3")
                    .header(ORIGIN, "localhost:8000")
                    .header(HOST, "localhost:8000")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(
            response.headers().get(ACCESS_CONTROL_ALLOW_ORIGIN).unwrap(),
            "localhost:8000"
        );

        let app = router(state.clone()).unwrap();
        let response = app
            .oneshot(
                Request::builder()
                    .uri("/api/v1/s3")
                    .header(ORIGIN, "http://example.com")
                    .header(HOST, "http://example.com")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(
            response.headers().get(ACCESS_CONTROL_ALLOW_ORIGIN).unwrap(),
            "http://example.com"
        );

        let app = router(state.clone()).unwrap();
        let response = app
            .oneshot(
                Request::builder()
                    .method(Method::OPTIONS)
                    .uri("/api/v1/s3")
                    .header(ORIGIN, "http://example.com")
                    .header(HOST, "http://example.com")
                    .header(ACCESS_CONTROL_REQUEST_METHOD, "GET")
                    .header(ACCESS_CONTROL_REQUEST_HEADERS, "Authorization")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(
            response.headers().get(ACCESS_CONTROL_ALLOW_ORIGIN).unwrap(),
            "http://example.com"
        );
        assert_eq!(
            response
                .headers()
                .get(ACCESS_CONTROL_ALLOW_METHODS)
                .unwrap(),
            "GET,HEAD,OPTIONS,POST,PATCH"
        );
        assert_eq!(
            response
                .headers()
                .get(ACCESS_CONTROL_ALLOW_HEADERS)
                .unwrap(),
            "authorization"
        );
    }
}
