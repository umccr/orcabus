//! This module handles API routing.
//!

use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use axum::routing::{get, post};
use axum::{Json, Router};
use sea_orm::{DbErr, RuntimeErr};
use serde::Serialize;
use sqlx::PgPool;
use std::sync::Arc;
use tower_http::trace::TraceLayer;
use utoipa::{IntoResponses, ToSchema};

use crate::database::Client;
use crate::env::Config;
use crate::error::Error;
use crate::routes::get::*;
use crate::routes::ingest::ingest_from_sqs;
use crate::routes::list::*;
use crate::routes::openapi::swagger_ui;

pub mod get;
mod ingest;
pub mod list;
pub mod openapi;

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

/// The main filemanager router for requests.
pub fn api_router(state: AppState) -> Router {
    Router::new()
        .route("/objects", get(list_objects))
        .route("/objects/:id", get(get_object_by_id))
        .route("/objects/count", get(count_objects))
        .route("/s3_objects", get(list_s3_objects))
        .route("/s3_objects/:id", get(get_s3_object_by_id))
        .route("/s3_objects/count", get(count_s3_objects))
        .route("/ingest_from_sqs", post(ingest_from_sqs))
        .fallback(fallback)
        .with_state(state)
        .layer(TraceLayer::new_for_http())
        .merge(swagger_ui())
}

/// The fallback route.
async fn fallback() -> impl IntoResponse {
    (
        StatusCode::NOT_FOUND,
        Json(ErrorResponse::new("not found".to_string())),
    )
        .into_response()
}

/// The error response format returned in the API.
#[derive(Debug, Serialize, ToSchema)]
pub struct ErrorResponse {
    message: String,
}

/// An enum representing http status code errors returned by the API.
#[derive(Debug, IntoResponses)]
pub enum ErrorStatusCode {
    #[response(
        status = BAD_REQUEST,
        description = "the request could not be parsed or the request triggered a logical error in the database",
        example = json!({"message": "Json Error: parsing json"}),
    )]
    BadRequest(ErrorResponse),
    #[response(
        status = INTERNAL_SERVER_ERROR,
        description = "an unexpected error occurred in the server",
        example = json!({"message": "Failed to acquire connection from pool: Connection pool timed out"}),
    )]
    InternalServerError(ErrorResponse),
    #[response(
        status = REQUEST_TIMEOUT,
        description = "the request could not be processed",
        example = json!({"message": "failed to update database credentials"}),
    )]
    RequestTimeout(ErrorResponse),
}

impl IntoResponse for ErrorStatusCode {
    fn into_response(self) -> Response {
        match self {
            ErrorStatusCode::BadRequest(err) => {
                (StatusCode::BAD_REQUEST, Json(err)).into_response()
            }
            ErrorStatusCode::InternalServerError(err) => {
                (StatusCode::INTERNAL_SERVER_ERROR, Json(err)).into_response()
            }
            ErrorStatusCode::RequestTimeout(err) => {
                (StatusCode::REQUEST_TIMEOUT, Json(err)).into_response()
            }
        }
    }
}

impl From<sqlx::Error> for ErrorStatusCode {
    fn from(err: sqlx::Error) -> Self {
        match err {
            sqlx::Error::RowNotFound
            | sqlx::Error::TypeNotFound { .. }
            | sqlx::Error::ColumnIndexOutOfBounds { .. }
            | sqlx::Error::ColumnNotFound(_) => Self::BadRequest(err.to_string().into()),
            _ => Self::InternalServerError(err.to_string().into()),
        }
    }
}

impl From<DbErr> for ErrorStatusCode {
    fn from(err: DbErr) -> Self {
        if let Some(err) = err.sql_err() {
            Self::BadRequest(ErrorResponse::new(err.to_string()))
        } else {
            match err {
                DbErr::Exec(RuntimeErr::SqlxError(err))
                | DbErr::Query(RuntimeErr::SqlxError(err))
                | DbErr::Conn(RuntimeErr::SqlxError(err)) => Self::from(err),
                DbErr::RecordNotFound(_)
                | DbErr::TryIntoErr { .. }
                | DbErr::Type(_)
                | DbErr::Json(_)
                | DbErr::RecordNotInserted
                | DbErr::RecordNotUpdated => Self::BadRequest(err.to_string().into()),
                _ => Self::InternalServerError(err.to_string().into()),
            }
        }
    }
}

impl From<Error> for ErrorStatusCode {
    fn from(err: Error) -> Self {
        match err {
            Error::DatabaseError(err) => Self::from(err),
            _ => Self::InternalServerError("unexpected error".to_string().into()),
        }
    }
}

impl From<String> for ErrorResponse {
    fn from(err: String) -> Self {
        ErrorResponse::new(err)
    }
}

impl ErrorResponse {
    /// Create an error response.
    pub fn new(message: String) -> Self {
        Self { message }
    }
}

impl IntoResponse for Error {
    fn into_response(self) -> Response {
        ErrorStatusCode::from(self).into_response()
    }
}

#[cfg(test)]
mod tests {
    use aws_lambda_events::http::Request;
    use axum::body::{to_bytes, Body};
    use axum::http::StatusCode;
    use axum::response::IntoResponse;
    use parquet::data_type::AsBytes;
    use sea_orm::DbErr;
    use serde_json::{from_slice, json, Value};
    use sqlx::PgPool;
    use tower::ServiceExt;

    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::error::Error;
    use crate::routes::{api_router, AppState};

    #[tokio::test]
    async fn sql_error_into_response() {
        let response =
            Error::DatabaseError(DbErr::Json("parsing json".to_string())).into_response();
        assert_eq!(response.status(), StatusCode::BAD_REQUEST);

        assert_eq!(
            json!({"message": "Json Error: parsing json"}),
            from_slice::<Value>(
                to_bytes(response.into_body(), usize::MAX)
                    .await
                    .unwrap()
                    .as_bytes()
            )
            .unwrap()
        );
    }

    #[tokio::test]
    async fn internal_error_into_response() {
        let response = Error::MigrateError("error".to_string()).into_response();
        assert_eq!(response.status(), StatusCode::INTERNAL_SERVER_ERROR);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn get_unknown_path(pool: PgPool) {
        let app = api_router(AppState::from_pool(pool));
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
