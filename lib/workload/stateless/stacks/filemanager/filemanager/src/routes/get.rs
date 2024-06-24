//! Route logic for get API calls.
//!

use crate::database::entities::object_group::Model as ObjectGroup;
use crate::database::entities::s3_object::Model as S3Object;
use crate::error::Result;
use crate::queries::get::GetQueryBuilder;
use crate::routes::AppState;
use axum::extract::{Path, State};
use axum::Json;
use serde::Deserialize;
use uuid::Uuid;

/// Params for a get object group by id request.
#[derive(Debug, Deserialize)]
pub struct GetObjectGroupById {}

/// The get object groups handler.
pub async fn get_object_group_by_id(
    state: State<AppState>,
    Path(id): Path<Uuid>,
) -> Result<Json<Option<ObjectGroup>>> {
    let query = GetQueryBuilder::new(&state.client);

    Ok(Json(query.get_object_group(id).await?))
}

/// Params for a get s3 objects by id request.
#[derive(Debug, Deserialize)]
pub struct GetS3ObjectById {}

/// The get s3 objects handler.
pub async fn get_s3_object_by_id(
    state: State<AppState>,
    Path(id): Path<Uuid>,
) -> Result<Json<Option<S3Object>>> {
    let query = GetQueryBuilder::new(&state.client);

    Ok(Json(query.get_s3_object_by_id(id).await?))
}
