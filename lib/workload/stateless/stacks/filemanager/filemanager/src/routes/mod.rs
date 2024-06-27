//! This module handles API routing.
//!

use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use axum::routing::get;
use axum::{Json, Router};
use serde::Serialize;

use crate::database::Client;
use crate::error::Error;
use crate::routes::get::{get_object_by_id, get_s3_object_by_id};
use crate::routes::list::{count_objects, count_s3_objects, list_objects, list_s3_objects};

pub mod get;
pub mod list;

#[derive(Debug, Clone)]
pub struct AppState {
    client: Client,
}

/// The main filemanager router for query read-only requests.
pub fn query_router(database: Client) -> Router {
    let state = AppState { client: database };

    Router::new()
        .route("/objects", get(list_objects))
        .route("/objects/:id", get(get_object_by_id))
        .route("/objects/count", get(count_objects))
        .route("/s3_objects", get(list_s3_objects))
        .route("/s3_objects/:id", get(get_s3_object_by_id))
        .route("/s3_objects/count", get(count_s3_objects))
        .with_state(state)
}

/// The error response format returned in the API.
#[derive(Serialize)]
pub struct ErrorResponse {
    message: String,
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

        (status, Json(ErrorResponse { message })).into_response()
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
