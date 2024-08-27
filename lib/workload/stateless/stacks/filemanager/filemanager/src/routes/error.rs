//! Error related parsing code specific to HTTP routes and responses.
//!

use std::fmt;
use std::fmt::{Debug, Display, Formatter};

use aws_lambda_events::http::StatusCode;
use axum::extract;
use axum::extract::rejection::{JsonRejection, PathRejection, QueryRejection};
use axum::response::{IntoResponse, Response};
use axum_extra::extract::WithRejection;
use sea_orm::DbErr;
use serde::{Deserialize, Serialize};
use serde_qs::axum::QsQueryRejection;
use thiserror::Error;
use utoipa::{IntoResponses, ToSchema};

use crate::error::Error;

/// Type alias for a Query with a custom rejection.
pub type Query<T> = WithRejection<extract::Query<T>, ErrorStatusCode>;

/// Type alias for a QsQuery with a custom rejection.
pub type QsQuery<T> = WithRejection<serde_qs::axum::QsQuery<T>, ErrorStatusCode>;

/// Type alias for a Path with a custom rejection.
pub type Path<T> = WithRejection<extract::Path<T>, ErrorStatusCode>;

/// Type alias for a Json with a custom rejection.
pub type Json<T> = WithRejection<extract::Json<T>, ErrorStatusCode>;

/// The fallback route, returns `NOT_FOUND`.
pub async fn fallback() -> impl IntoResponse {
    (
        StatusCode::NOT_FOUND,
        extract::Json(ErrorResponse::new("not found".to_string())),
    )
        .into_response()
}

/// The error response format returned in the API.
#[derive(Debug, Serialize, ToSchema, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ErrorResponse {
    message: String,
}

impl Display for ErrorResponse {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        f.write_str(&self.message)
    }
}

/// An enum representing http status code errors returned by the API.
#[derive(Debug, IntoResponses, Error)]
pub enum ErrorStatusCode {
    #[response(status = BAD_REQUEST)]
    #[error(transparent)]
    QueryRejection(#[from] QueryRejection),
    #[response(status = BAD_REQUEST)]
    #[error(transparent)]
    QsQueryRejection(#[from] QsQueryRejection),
    #[response(status = BAD_REQUEST)]
    #[error(transparent)]
    PathRejection(#[from] PathRejection),
    #[response(status = BAD_REQUEST)]
    #[error(transparent)]
    JsonRejection(#[from] JsonRejection),
    #[response(
        status = NOT_FOUND,
        description = "the resource or route could not be found",
        example = json!({"message": "expected record for id: `00000000-0000-0000-0000-000000000000`"}),
    )]
    NotFound(ErrorResponse),
    #[response(
        status = INTERNAL_SERVER_ERROR,
        description = "an unexpected error occurred in the server",
        example = json!({"message": "Failed to acquire connection from pool: Connection pool timed out"}),
    )]
    InternalServerError(ErrorResponse),
    #[response(
        status = BAD_REQUEST,
        description = "the request could not be parsed or the request triggered a constraint error in the database",
        example = json!({"message": "JSON Error: parsing json"}),
    )]
    BadRequest(ErrorResponse),
}

impl Display for ErrorStatusCode {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        match self {
            ErrorStatusCode::BadRequest(err) => Display::fmt(err, f),
            ErrorStatusCode::NotFound(err) => Display::fmt(err, f),
            ErrorStatusCode::InternalServerError(err) => Display::fmt(err, f),
            ErrorStatusCode::QueryRejection(rejection) => Display::fmt(rejection, f),
            ErrorStatusCode::QsQueryRejection(rejection) => Display::fmt(rejection, f),
            ErrorStatusCode::PathRejection(rejection) => Display::fmt(rejection, f),
            ErrorStatusCode::JsonRejection(rejection) => Display::fmt(rejection, f),
        }
    }
}

impl IntoResponse for ErrorStatusCode {
    fn into_response(self) -> Response {
        let response = match self {
            ErrorStatusCode::BadRequest(err) => (StatusCode::BAD_REQUEST, extract::Json(err)),
            ErrorStatusCode::InternalServerError(err) => {
                (StatusCode::INTERNAL_SERVER_ERROR, extract::Json(err))
            }
            ErrorStatusCode::NotFound(err) => (StatusCode::NOT_FOUND, extract::Json(err)),
            ErrorStatusCode::QueryRejection(rejection) => (
                rejection.status(),
                extract::Json(ErrorResponse::new(rejection.body_text())),
            ),
            ErrorStatusCode::QsQueryRejection(rejection) => {
                let message = rejection.to_string();
                let status = rejection.into_response().status();

                (status, extract::Json(ErrorResponse::new(message)))
            }
            ErrorStatusCode::PathRejection(rejection) => (
                rejection.status(),
                extract::Json(ErrorResponse::new(rejection.body_text())),
            ),
            ErrorStatusCode::JsonRejection(rejection) => (
                rejection.status(),
                extract::Json(ErrorResponse::new(rejection.body_text())),
            ),
        };

        response.into_response()
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
            Error::InvalidQuery(_) | Error::ParseError(_) | Error::MissingHostHeader => {
                Self::BadRequest(err.to_string().into())
            }
            Error::QueryError(_) | Error::SerdeError(_) | Error::PresignedUrlError(_) => {
                Self::InternalServerError(err.to_string().into())
            }
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
