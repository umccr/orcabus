//! Route logic for list API calls.
//!

use crate::database::entities::object_group::Model as ObjectGroup;
use crate::error::Result;
use crate::queries::list::ListQueryBuilder;
use crate::routes::AppState;
use axum::extract::State;
use axum::Json;
use serde::Deserialize;

/// Params for a list object request.
#[derive(Debug, Deserialize)]
pub struct ListObjectGroupsParams {}

/// The list object handler.
pub async fn list_object_groups(state: State<AppState>) -> Result<Json<Vec<ObjectGroup>>> {
    let query = ListQueryBuilder::new(&state.client);

    Ok(Json(query.list_object_groups().await?))
}
