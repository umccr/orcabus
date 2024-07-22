use crate::database::entities::object::Model as FileObject;
use crate::database::entities::s3_object::Model as FileS3Object;
use crate::error::Error::APIError;
use crate::error::Result;
use crate::queries::update::UpdateQueryBuilder;
use crate::routes::ErrorStatusCode::BadRequest;
use crate::routes::{AppState, ErrorResponse, ErrorStatusCode};
use axum::extract::{Path, Query, State};
use axum::Json;
use sea_orm::TransactionTrait;
use serde::Deserialize;
use serde_json::{Map, Value};
use utoipa::{IntoParams, ToSchema};
use uuid::Uuid;

/// The type of merge strategy to use when updating attributes.
#[derive(Debug, Default, Deserialize, ToSchema)]
pub enum MergeStrategy {
    /// Insert the attributes and return a 400 error if any of the keys already exist.
    /// This does not update any keys if an error is returned, even if some of those
    /// keys do not conflict with the attributes. 
    #[default]
    Insert,
    /// Insert the attributes only for keys that do not already exist without returning
    /// an error. Does not update the keys that do exist. This results in a partial update
    /// where only the non-conflicting keys are inserted.
    InsertNonExistent,
    /// Insert the attributes if the keys do not exist or replace the existing attributes
    /// under the same key if they do exist.
    Replace,
}

/// The attributes to update for the request. This gets merged into the existing attributes
/// according to the `MergeStrategy`. The body of the request must be a valid JSON
/// Object type in order to perform merging. That is, the outer type of the JSON input
/// must be an Object with at least one key, e.g.
///
/// ```json
/// {
///     "attribute_id": "id"
/// }
/// ```
///
/// This means that other JSON types in the outer JSON body are not supported. It's not possible
/// to merge outer array types, however arrays inside an Object type are supported. E.g. this will
/// return an error:
///
/// ```json
/// ["1", "2", "3"]
/// ```
///
/// And this is a valid request:
///
/// ```json
/// {
///     "some_array": ["1", "2", "3"]
/// }
/// ```
#[derive(Debug, Deserialize, Default)]
pub struct AttributeBody(Map<String, Value>);

impl AttributeBody {
    /// Create a new attribute body.
    pub fn new(inner: Map<String, Value>) -> Self {
        Self(inner)
    }

    /// Get the inner map.
    pub fn into_inner(self) -> Map<String, Value> {
        self.0
    }
    
    /// Get the inner JSON object.
    pub fn into_object(self) -> Value {
        Value::Object(self.0)
    }
}

/// Params for an update to attributes.
#[derive(Debug, Deserialize, Default, IntoParams)]
#[serde(default)]
#[into_params(parameter_in = Query)]
pub struct UpdateAttributesParams {
    /// The type of merge strategy to use when updating attributes.
    #[param(nullable)]
    merge_strategy: MergeStrategy,
}

/// Update the object attributes using a patch request.
#[utoipa::path(
    patch,
    path = "/objects/{id}",
    responses(
        (status = OK, description = "Update the object attributes", body = FileObject),
        ErrorStatusCode,
    ),
    params(UpdateAttributesParams),
    request_body = AttributeBody,
    context_path = "/api/v1",
)]
pub async fn update_object_attributes(
    state: State<AppState>,
    Path(id): Path<Uuid>,
    Query(update_attributes): Query<UpdateAttributesParams>,
    Json(request): Json<AttributeBody>,
) -> Result<Json<FileObject>> {
    match update_attributes.merge_strategy {
        MergeStrategy::Insert => {
            unimplemented!()
        }
        MergeStrategy::InsertNonExistent => {
            let query = 
              UpdateQueryBuilder::new(state.client.connection_ref())
                .update_attributes_insert(request);

            Ok(Json(query.one().await?.ok_or_else(|| {
                APIError(BadRequest(ErrorResponse {
                    message: format!("object with id {} not found", id),
                }))
            })?))
        }
        MergeStrategy::Replace => {
            let query = 
              UpdateQueryBuilder::new(state.client.connection_ref())
              .update_attributes_replace(request);

            Ok(Json(query.one().await?.ok_or_else(|| {
                APIError(BadRequest(ErrorResponse {
                    message: format!("object with id {} not found", id),
                }))
            })?))
        }
    }
}
