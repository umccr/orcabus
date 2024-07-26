//! Error related parsing code specific to HTTP routes and responses.
//!

use crate::error::Error;
use aws_lambda_events::http::StatusCode;
use axum::response::{IntoResponse, Response};
use axum::Json;
use sea_orm::DbErr;
use serde::Serialize;
use utoipa::{IntoResponses, ToSchema};

/// The fallback route, returns `NOT_FOUND`.
pub async fn fallback() -> impl IntoResponse {
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
        description = "the request could not be parsed or the request triggered a constraint error in the database",
        example = json!({"message": "JSON Error: parsing json"}),
    )]
    BadRequest(ErrorResponse),
    #[response(
        status = NOT_FOUND,
        description = "the resource or route could not be found",
        example = json!({"message": "expected some value for id: `00000000-0000-0000-0000-000000000000`"}),
    )]
    NotFound(ErrorResponse),
    #[response(
        status = INTERNAL_SERVER_ERROR,
        description = "an unexpected error occurred in the server",
        example = json!({"message": "Failed to acquire connection from pool: Connection pool timed out"}),
    )]
    InternalServerError(ErrorResponse),
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
            ErrorStatusCode::NotFound(err) => (StatusCode::NOT_FOUND, Json(err)).into_response(),
        }
    }
}

impl From<DbErr> for ErrorStatusCode {
    fn from(err: DbErr) -> Self {
        if let Some(err) = err.sql_err() {
            Self::BadRequest(ErrorResponse::new(err.to_string()))
        } else {
            Self::InternalServerError(err.to_string().into())
        }
    }
}

impl From<Error> for ErrorStatusCode {
    fn from(err: Error) -> Self {
        match err {
            Error::DatabaseError(err) => Self::from(err),
            Error::OverflowError | Error::ConversionError(_) => {
                Self::BadRequest(err.to_string().into())
            }
            Error::InvalidQuery(_) => Self::BadRequest(err.to_string().into()),
            Error::QueryError(_) => Self::InternalServerError(err.to_string().into()),
            Error::ExpectedSomeValue(_) => Self::NotFound(err.to_string().into()),
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
