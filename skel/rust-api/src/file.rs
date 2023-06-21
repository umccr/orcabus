use axum::{extract::Query, Json};
use serde::{Deserialize, Serialize};
use utoipa::{IntoParams, ToSchema};

use tracing::info;
//type Store = Mutex<Vec<File>>;
// TODO: SQLx is the store backend, through db.rs

/// Item to do.
#[derive(Serialize, Deserialize, ToSchema, IntoParams, Clone)]
pub struct File {
    id: i32,
    #[schema(example = "foo.bam")]
    name: String,
    size: u64,
    hash: String,
}

/// File operation errors
#[derive(Serialize, Deserialize, ToSchema)]
pub enum FileError {
    /// File not found by id.
    #[schema(example = "id = 1")]
    NotFound(String),
    /// File operation unauthorized
    #[schema(example = "missing api key")]
    Unauthorized(String),
}

/// Search query
// #[derive(Debug, Deserialize, IntoParams)]
// pub struct FileQuery {
//     id:
//     name: String,
// }

/// Search files
#[utoipa::path(
    get,
    path = "/file/",
    params(
        //FileQuery
        File
    ),
    responses(
        (status = 200, description = "List matching objects", body = [File])
    )
)]
pub async fn search(query: Query<File>) -> Json<Vec<File>> {
    info!("searching {:?}", query.name);
    Json(vec![File {
        id: 1,
        name: query.name.clone(),
        size: 1,
        hash: "Moo".to_string(),
    }])
}
