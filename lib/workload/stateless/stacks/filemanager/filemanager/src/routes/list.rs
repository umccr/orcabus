//! Route logic for list API calls.
//!

use crate::database::entities::object_group::Model as ObjectGroup;
use crate::database::entities::s3_object::Model as S3Object;
use crate::error::Result;
use crate::queries::list::ListQueryBuilder;
use crate::routes::AppState;
use axum::extract::State;
use axum::Json;
use serde::Deserialize;

/// Params for a list object groups request.
#[derive(Debug, Deserialize)]
pub struct ListObjectGroupsParams {}

/// The list object groups handler.
pub async fn list_object_groups(state: State<AppState>) -> Result<Json<Vec<ObjectGroup>>> {
    let query = ListQueryBuilder::new(&state.client);

    Ok(Json(query.list_object_groups().await?))
}

/// The count object groups handler.
pub async fn count_object_groups(state: State<AppState>) -> Result<Json<u64>> {
    let query = ListQueryBuilder::new(&state.client);

    Ok(Json(query.count_object_groups().await?))
}

/// Params for a list s3 objects request.
#[derive(Debug, Deserialize)]
pub struct ListS3ObjectsParams {}

/// The list s3 objects handler.
pub async fn list_s3_objects(state: State<AppState>) -> Result<Json<Vec<S3Object>>> {
    let query = ListQueryBuilder::new(&state.client);

    Ok(Json(query.list_s3_objects().await?))
}

/// The count s3 objects handler.
pub async fn count_s3_objects(state: State<AppState>) -> Result<Json<u64>> {
    let query = ListQueryBuilder::new(&state.client);

    Ok(Json(query.count_s3_objects().await?))
}
