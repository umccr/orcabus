//! This module handles API routing.
//!

pub mod get;
pub mod list;

use crate::database::Client;
use crate::error::Error;
use crate::routes::get::{get_object_group_by_id, get_s3_object_by_id};
use crate::routes::list::{list_object_groups, list_s3_objects};
use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use axum::routing::get;
use axum::{Json, Router};
use serde::Serialize;

#[derive(Debug, Clone)]
pub struct AppState {
    client: Client,
}

/// The main filemanager router for query read-only requests.
pub fn query_router(database: Client) -> Router {
    let state = AppState { client: database };

    Router::new()
        .route("/object_groups", get(list_object_groups))
        .route("/object_groups/:id", get(get_object_group_by_id))
        .route("/s3_objects", get(list_s3_objects))
        .route("/s3_objects/:id", get(get_s3_object_by_id))
        .with_state(state)
}

/// The errro response format returned in the API.
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
