use axum::{extract::Query, Json};
use serde::{Deserialize, Serialize};
use utoipa::{IntoParams, ToSchema};

use tracing::{ info };
//type Store = Mutex<Vec<FileManager>>;
// TODO: SQLx is the store backend, through db.rs

/// Item to do.
#[derive(Serialize, Deserialize, ToSchema, Clone)]
pub struct FileManager {
    id: i32,
    #[schema(example = "foo.bam")]
    name: String,
}

/// Filemanager operation errors
#[derive(Serialize, Deserialize, ToSchema)]
pub enum FileManagerError {
    /// File not found by id.
    #[schema(example = "id = 1")]
    NotFound(String),
    /// Filemanager operation unauthorized
    #[schema(example = "missing api key")]
    Unauthorized(String),
}

/// Search query
#[derive(Debug, Deserialize, IntoParams)]
pub struct FileQuery {
    value: String,
}

/// Search files
#[utoipa::path(
    get,
    path = "/filemanager/",
    params(
        FileQuery
    ),
    responses(
        (status = 200, description = "List matching objects", body = [FileManager])
    )
)]
pub async fn search(query: Query<FileQuery>) -> Json<Vec<FileManager>> {
    info!("searching {:?}", query);
    Json(vec![FileManager {
        id: 1,
        name: query.value.clone(),
    }])
}
