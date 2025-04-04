//! This module handles API routing.
//!

use std::collections::HashSet;
use std::sync::Arc;

use crate::database::entities::s3_crawl::Model as Crawl;
use axum::http::header::InvalidHeaderName;
use axum::http::method::InvalidMethod;
use axum::http::HeaderValue;
use axum::{Extension, Json, Router};
use chrono::Duration;
use serde_qs::axum::QsQueryConfig;
use sqlx::PgPool;
use tokio::sync::Mutex;
use tokio::task::JoinHandle;
use tower_http::cors::CorsLayer;
use tower_http::trace::TraceLayer;
use tracing::trace;

use crate::clients::aws::{s3, secrets_manager, sqs};
use crate::database;
use crate::env::Config;
use crate::error::Error::{ApiConfigurationError, CrawlError};
use crate::error::Result;
use crate::routes::crawl::crawl_router;
use crate::routes::error::fallback;
use crate::routes::get::*;
use crate::routes::ingest::ingest_router;
use crate::routes::list::*;
use crate::routes::openapi::swagger_ui;
use crate::routes::update::update_router;

pub mod crawl;
pub mod error;
pub mod filter;
pub mod get;
pub mod header;
pub mod ingest;
pub mod list;
pub mod openapi;
pub mod pagination;
pub mod presign;
pub mod update;

/// The join handle crawl task.
pub type CrawlTask = JoinHandle<Result<Json<Crawl>>>;

/// App state containing database client.
#[derive(Clone)]
pub struct AppState {
    database_client: database::Client,
    config: Arc<Config>,
    s3_client: Arc<s3::Client>,
    sqs_client: Arc<sqs::Client>,
    secrets_manager_client: Arc<secrets_manager::Client>,
    use_tls_links: bool,
    params_field_names: Arc<HashSet<String>>,
    crawl_task: Arc<Mutex<Option<CrawlTask>>>,
}

impl AppState {
    /// Create new state.
    pub fn new(
        database_client: database::Client,
        config: Arc<Config>,
        s3_client: Arc<s3::Client>,
        sqs_client: Arc<sqs::Client>,
        secrets_manager_client: Arc<secrets_manager::Client>,
        use_tls_links: bool,
    ) -> Self {
        Self {
            database_client,
            config,
            s3_client,
            sqs_client,
            secrets_manager_client,
            use_tls_links,
            params_field_names: Arc::new(attributes_s3_field_names()),
            crawl_task: Arc::new(Mutex::new(None)),
        }
    }

    /// Create a new state from an existing pool with default config.
    pub async fn from_pool(pool: PgPool) -> Result<Self> {
        Ok(Self::new(
            database::Client::from_pool(pool),
            Default::default(),
            Arc::new(s3::Client::with_defaults().await),
            Arc::new(sqs::Client::with_defaults().await),
            Arc::new(secrets_manager::Client::with_defaults().await?),
            false,
        ))
    }

    /// Modify the field names for parameters.
    pub fn with_params_field_names(mut self, params_field_names: Arc<HashSet<String>>) -> Self {
        self.params_field_names = params_field_names;
        self
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

    /// Get the s3 client.
    pub fn s3_client(&self) -> &s3::Client {
        &self.s3_client
    }

    /// Get the secrets manager client.
    pub fn secrets_manager_client(&self) -> &secrets_manager::Client {
        &self.secrets_manager_client
    }

    /// Get the sqs client.
    pub fn sqs_client(&self) -> &sqs::Client {
        &self.sqs_client
    }

    /// Get the links TLS setting.
    pub fn use_tls_links(&self) -> bool {
        self.use_tls_links
    }

    /// Get the crawl task result.
    pub async fn into_crawl_result(self) -> Result<Json<Crawl>> {
        let mut task = self.crawl_task.lock().await;
        let task = task
            .take()
            .ok_or_else(|| CrawlError("missing task".to_string()))?;

        task.await.map_err(|err| CrawlError(err.to_string()))?
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
pub fn cors_layer(config: &Config) -> Result<CorsLayer> {
    let mut layer = CorsLayer::new()
        .allow_headers(
            config
                .api_cors_allow_headers()
                .iter()
                .map(|method| {
                    method
                        .parse()
                        .map_err(|err: InvalidHeaderName| ApiConfigurationError(err.to_string()))
                })
                .collect::<Result<Vec<_>>>()?,
        )
        .allow_methods(
            config
                .api_cors_allow_methods()
                .iter()
                .map(|method| {
                    method
                        .parse()
                        .map_err(|err: InvalidMethod| ApiConfigurationError(err.to_string()))
                })
                .collect::<Result<Vec<_>>>()?,
        )
        .max_age(
            Duration::days(10)
                .to_std()
                .map_err(|err| ApiConfigurationError(err.to_string()))?,
        );

    if let Some(origins) = config.api_cors_allow_origins() {
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
        .merge(crawl_router())
        .layer(Extension(QsQueryConfig::new(5, false)))
        .layer(cors_layer(state.config())?)
        .layer(TraceLayer::new_for_http())
        .with_state(state))
}

#[cfg(test)]
mod tests {
    use std::sync::Arc;

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
    use tower::util::ServiceExt;

    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::env::Config;
    use crate::error::Error;
    use crate::routes::{router, AppState};

    #[tokio::test]
    async fn internal_error_into_response() {
        let response = Error::MigrateError("error".to_string()).into_response();
        assert_eq!(response.status(), StatusCode::INTERNAL_SERVER_ERROR);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn get_unknown_path(pool: PgPool) {
        let app = router(AppState::from_pool(pool).await.unwrap()).unwrap();
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
        let mut state = AppState::from_pool(pool).await.unwrap();
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
