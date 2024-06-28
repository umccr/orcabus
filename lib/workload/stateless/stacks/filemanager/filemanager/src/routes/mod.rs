//! This module handles API routing.
//!

use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use axum::{Json, Router};
use axum_extra::routing::RouterExt;
use serde::Serialize;
use tower_http::trace::TraceLayer;
use utoipa::OpenApi;
use utoipa_swagger_ui::SwaggerUi;

use crate::database::Client;
use crate::error::Error;
use crate::routes::get::*;
use crate::routes::list::*;

pub mod get;
pub mod list;

/// API docs.
#[derive(OpenApi)]
#[openapi(paths(
    list_objects,
    get_object_by_id,
    count_objects,
    list_s3_objects,
    get_s3_object_by_id,
    count_s3_objects
))]
pub struct ApiDoc;

/// App state containing database client.
#[derive(Debug, Clone)]
pub struct AppState {
    client: Client,
}

/// The main filemanager router for query read-only requests.
pub fn query_router(client: Client) -> Router {
    let state = AppState { client };

    Router::new()
        .typed_get(list_objects)
        .typed_get(get_object_by_id)
        .typed_get(count_objects)
        .typed_get(list_s3_objects)
        .typed_get(get_s3_object_by_id)
        .typed_get(count_s3_objects)
        .fallback(fallback)
        .with_state(state)
        .layer(TraceLayer::new_for_http())
        .merge(SwaggerUi::new("/swagger_ui").url("/api_docs/openapi.json", ApiDoc::openapi()))
}

/// The fallback route.
async fn fallback() -> impl IntoResponse {
    ErrorResponse::new("not found".to_string()).response(StatusCode::NOT_FOUND)
}

/// The error response format returned in the API.
#[derive(Serialize)]
pub struct ErrorResponse {
    message: String,
}

impl ErrorResponse {
    /// Create an error response.
    pub fn new(message: String) -> Self {
        Self { message }
    }

    /// Create the response from this error.
    pub fn response(self, status_code: StatusCode) -> impl IntoResponse {
        (status_code, Json(self)).into_response()
    }
}

impl IntoResponse for Error {
    fn into_response(self) -> Response {
        let (status, message) = match self {
            Error::SQLError(err) => (StatusCode::NOT_FOUND, err.to_string()),
            _ => (
                StatusCode::INTERNAL_SERVER_ERROR,
                "unexpected error".to_string(),
            ),
        };

        ErrorResponse::new(message).response(status).into_response()
    }
}

#[cfg(test)]
mod tests {
    use axum::body::to_bytes;
    use axum::http::StatusCode;
    use axum::response::IntoResponse;
    use parquet::data_type::AsBytes;
    use serde_json::{from_slice, json, Value};

    use crate::error::Error;

    #[tokio::test]
    async fn sql_error_into_response() {
        let response = Error::SQLError("error".to_string()).into_response();
        assert_eq!(response.status(), StatusCode::NOT_FOUND);

        assert_eq!(
            json!({"message": "error"}),
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
}
