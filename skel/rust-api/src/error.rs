use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use axum::Json;
use serde_json::json;
use std::result;
use thiserror::Error;

pub type Result<T> = result::Result<T, Error>;

#[derive(Error, Debug)]
pub enum Error {
    /// File not found by id.
    #[error("file not found: `{0}`")]
    NotFound(String),
    /// File operation unauthorized
    #[error("unauthorized: `{0}`")]
    Unauthorized(String),
}

impl IntoResponse for Error {
    fn into_response(self) -> Response {
        let (status, error_message) = match self {
            Self::NotFound(err) => (StatusCode::NOT_FOUND, err),
            Self::Unauthorized(err) => (StatusCode::UNAUTHORIZED, err),
        };

        let body = Json(json!({
            "error": error_message,
        }));

        (status, body).into_response()
    }
}
