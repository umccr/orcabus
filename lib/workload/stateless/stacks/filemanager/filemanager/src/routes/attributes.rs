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
///     "attributes": {
///         "attribute_id": "id"
///     }
/// }
/// ```
///
/// This means that other JSON types in the outer JSON body are not supported. It's not possible
/// to merge outer array types, however arrays inside an Object type are supported. E.g. this will
/// return an error:
///
/// ```json
/// {
///     "attributes": ["1", "2", "3"]
/// }
/// ```
///
/// And this is a valid request:
///
/// ```json
/// {
///     "attributes": {
///         "some_array": ["1", "2", "3"]
///     }
/// }
/// ```
#[derive(Debug, Deserialize, Default, Clone)]
pub struct AttributeBody {
    attributes: Map<String, Value>,
}

impl AttributeBody {
    /// Create a new attribute body.
    pub fn new(attributes: Map<String, Value>) -> Self {
        Self { attributes }
    }

    /// Get the inner map.
    pub fn into_inner(self) -> Map<String, Value> {
        self.attributes
    }

    /// Get the inner JSON object.
    pub fn into_object(self) -> Value {
        Value::Object(self.attributes)
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
            let txn = state.client().connection_ref().begin().await?;

            let model = UpdateQueryBuilder::new(&txn)
                .update_attributes_insert(request.clone())
                .one()
                .await?
                .ok_or_else(|| {
                    APIError(BadRequest(ErrorResponse {
                        message: format!("object with id {} not found", id),
                    }))
                })?;

            let merged = model.clone().attributes.unwrap_or_default();

            let default = Default::default();
            let merged = merged.as_object().unwrap_or(&default);

            // Find whether this update had conflicting keys.
            let conflict = request
                .into_inner()
                .into_iter()
                .map(|(key, value)| {
                    // If the new merged value does not equal the requested update attributes
                    // then this means that the same key was present in the existing attributes.
                    merged
                        .get(&key)
                        .map(|merged_value| merged_value != &value)
                        .unwrap_or_default()
                })
                .find(|value| *value)
                .unwrap_or_default();

            if conflict {
                txn.rollback().await?;
                Err(APIError(BadRequest(ErrorResponse {
                    message: "insert request contains keys which already exist in the object"
                        .to_string(),
                })))
            } else {
                txn.commit().await?;
                Ok(Json(model))
            }
        }
        MergeStrategy::InsertNonExistent => {
            let query = UpdateQueryBuilder::new(state.client.connection_ref())
                .update_attributes_insert(request);

            Ok(Json(query.one().await?.ok_or_else(|| {
                APIError(BadRequest(ErrorResponse {
                    message: format!("object with id {} not found", id),
                }))
            })?))
        }
        MergeStrategy::Replace => {
            let query = UpdateQueryBuilder::new(state.client.connection_ref())
                .update_attributes_replace(request);

            Ok(Json(query.one().await?.ok_or_else(|| {
                APIError(BadRequest(ErrorResponse {
                    message: format!("object with id {} not found", id),
                }))
            })?))
        }
    }
}

#[cfg(test)]
mod tests {
    use axum::body::Body;
    use axum::http::{Method, StatusCode};
    use serde_json::json;
    use sqlx::PgPool;

    use super::*;
    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::entities::object::{
        ActiveModel as ObjectActiveModel, Entity as ObjectEntity,
    };
    use crate::database::entities::s3_object::Entity as S3ObjectEntity;
    use crate::queries::get::GetQueryBuilder;
    use crate::queries::tests::initialize_database;
    use crate::routes::list::tests::response_from;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_object_attributes_api_insert(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = initialize_database(state.client(), 10).await.objects;

        let mut first = entries[0].clone();
        let body = json!({
            "attributes": {
                // An existing attribute should cause a conflict.
                "attribute_id": {
                    "nested_id": "attribute_id"
                },
                "another_id": "attribute_id"
            }
        })
        .to_string();

        let (status_code, _) = response_from::<Value>(
            state.clone(),
            &format!("/objects/{}", first.object_id),
            Method::PATCH,
            Body::new(body),
        )
        .await;
        assert_eq!(status_code, StatusCode::BAD_REQUEST);

        // The state of the database should not have changed because a rollback is performed.
        let current_object = GetQueryBuilder::new(state.client())
            .get_object(first.object_id)
            .await
            .unwrap()
            .unwrap();
        assert_eq!(current_object, first);

        let body = json!({
            "attributes": {
                // A completely new attribute should successfully update.
                "another_id": "attribute_id"
            }
        })
        .to_string();
        let (_, result) = response_from::<FileObject>(
            state.clone(),
            &format!("/objects/{}", first.object_id),
            Method::PATCH,
            Body::new(body),
        )
        .await;

        first.attributes.as_mut().unwrap()["another_id"] = json!("attribute_id");
        assert_eq!(result, first);

        // The state of the database should have the new attributes now.
        let current_object = GetQueryBuilder::new(state.client())
            .get_object(first.object_id)
            .await
            .unwrap()
            .unwrap();
        assert_eq!(current_object, first);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_object_attributes_api_insert_non_existent(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = initialize_database(state.client(), 10).await.objects;

        let mut first = entries[0].clone();
        let body = json!({
            "attributes": {
                // An existing attribute should not overwrite.
                "attribute_id": {
                    "nested_id": "attribute_id"
                },
                // A new attribute should update normally.
                "another_id": "attribute_id"
            }
        })
        .to_string();

        let (_, result) = response_from::<FileObject>(
            state,
            &format!(
                "/objects/{}?merge_strategy=InsertNonExistent",
                first.object_id
            ),
            Method::PATCH,
            Body::new(body),
        )
        .await;

        first.attributes.as_mut().unwrap()["another_id"] = json!("attribute_id");
        assert_eq!(result, first);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_object_attributes_api_replace(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = initialize_database(state.client(), 10).await.objects;

        let mut first = entries[0].clone();
        let body = json!({
            "attributes": {
                // An existing attribute should overwrite.
                "attribute_id": {
                    "nested_id": "attribute_id"
                }
            }
        })
        .to_string();

        let (_, result) = response_from::<FileObject>(
            state,
            &format!("/objects/{}?merge_strategy=Replace", first.object_id),
            Method::PATCH,
            Body::new(body),
        )
        .await;
        first.attributes.as_mut().unwrap()["attribute_id"] = json!({"nested_id": "attribute_id"});

        assert_eq!(result, first);
    }
}
