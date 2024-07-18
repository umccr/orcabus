use crate::database::entities::object::Model as FileObject;
use crate::database::entities::s3_object::Model as FileS3Object;
use crate::error::Error::APIError;
use crate::error::Result;
use crate::queries::update::UpdateQueryBuilder;
use crate::routes::ErrorStatusCode::BadRequest;
use crate::routes::{AppState, ErrorResponse, ErrorStatusCode};
use axum::extract::{Path, Query, State};
use axum::Json;
use serde::Deserialize;
use serde_json::{Map, Value};
use utoipa::{IntoParams, ToSchema};
use uuid::Uuid;

/// The type of merge strategy to use when updating attributes.
#[derive(Debug, Default, Deserialize, ToSchema)]
pub enum MergeStrategy {
    /// Insert the attributes and return a 400 error if the attribute key already exists.
    #[default]
    Insert,
    /// Insert the attributes only if the key does not already exist. Does not update
    /// the attributes if the key does exist and no error is returned.
    InsertIfNotExists,
    /// Insert the attributes if the key does not exist or replace the existing attributes
    /// under the same key if it does exist.
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

    /// Get the inner JSON value.
    pub fn into_inner(self) -> Value {
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
    let query = UpdateQueryBuilder::new(&state.client);

    match update_attributes.merge_strategy {
        MergeStrategy::Insert => {
            unimplemented!()
        }
        MergeStrategy::InsertIfNotExists => {
            unimplemented!()
        }
        MergeStrategy::Replace => {
            let query = query.update_attributes_replace(request);

            Ok(Json(query.one().await?.ok_or_else(|| {
                APIError(BadRequest(ErrorResponse {
                    message: format!("object with id {} not found", id),
                }))
            })?))
        }
    }
}
