use axum::extract::{Path, Query, State};
use axum::Json;
use sea_orm::TransactionTrait;
use serde::Deserialize;
use serde_json::{Map, Value};
use serde_qs::axum::QsQuery;
use utoipa::{IntoParams, ToSchema};
use uuid::Uuid;

use crate::database::entities::object::Model as FileObject;
use crate::error::Error::APIError;
use crate::error::Result;
use crate::queries::update::UpdateQueryBuilder;
use crate::routes::filtering::ObjectsFilterAll;
use crate::routes::ErrorStatusCode::BadRequest;
use crate::routes::{AppState, ErrorResponse, ErrorStatusCode};

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

    /// Get the inner map as a reference
    pub fn get_ref(&self) -> &Map<String, Value> {
        &self.attributes
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
        (
            status = OK,
            description = "Update a single object's attributes returning the object",
            body = FileObject
        ),
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
    // Dropped transaction will automatically rollback.
    let txn = state.client().connection_ref().begin().await?;

    let results = UpdateQueryBuilder::new(&txn)
        .for_id(id)
        .for_objects(request, update_attributes.merge_strategy)
        .await?
        .into_iter()
        .next()
        .ok_or_else(|| {
            APIError(BadRequest(ErrorResponse {
                message: format!("object with id {} not found", id),
            }))
        })?;

    txn.commit().await?;

    Ok(Json(results))
}

/// Update the attributes for a collection of objects using a patch request. This
/// updates all attributes matching filter params with a set of the same attributes.
#[utoipa::path(
    patch,
    path = "/objects",
    responses(
        (
            status = OK,
            description = "Update attributes for a collection of objects returning the updated attributes",
            body = Vec<FileObject>
        ),
        ErrorStatusCode,
    ),
    params(UpdateAttributesParams, ObjectsFilterAll),
    request_body = AttributeBody,
    context_path = "/api/v1",
)]
pub async fn update_object_collection_attributes(
    state: State<AppState>,
    Query(update_attributes): Query<UpdateAttributesParams>,
    QsQuery(filter_all): QsQuery<ObjectsFilterAll>,
    Json(request): Json<AttributeBody>,
) -> Result<Json<Vec<FileObject>>> {
    // Dropped transaction will automatically rollback.
    let txn = state.client().connection_ref().begin().await?;

    let results = UpdateQueryBuilder::new(&txn)
        .filter_all(filter_all)
        .for_objects(request, update_attributes.merge_strategy)
        .await?;

    txn.commit().await?;

    Ok(Json(results))
}

#[cfg(test)]
mod tests {
    use axum::body::Body;
    use axum::http::Method;
    use serde_json::json;
    use sqlx::PgPool;

    use super::*;
    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::queries::tests::initialize_database;
    use crate::queries::update::tests::assert_correct_records;
    use crate::routes::list::tests::response_from;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_object_attributes_api_insert(_pool: PgPool) {
        // let state = AppState::from_pool(pool);
        // let entries = initialize_database(state.client(), 10).await.objects;
        //
        // let mut first = entries[0].clone();
        // let body = json!({
        //     "attributes": {
        //         // An existing attribute should cause a conflict.
        //         "attribute_id": {
        //             "nested_id": "attribute_id"
        //         },
        //         "another_id": "attribute_id"
        //     }
        // })
        // .to_string();
        //
        // let (status_code, _) = response_from::<Value>(
        //     state.clone(),
        //     &format!("/objects/{}", first.object_id),
        //     Method::PATCH,
        //     Body::new(body),
        // )
        // .await;
        // assert_eq!(status_code, StatusCode::BAD_REQUEST);
        //
        // change_attributes(state.client(), &entries[1], &json!({
        //     "attribute_id": "1"
        // }).to_string()).await;
        //
        // let body = json!({
        //     "attributes": {
        //         // An existing attribute should cause a conflict.
        //         "nested_id": {
        //             "attribute_id": "attribute_id"
        //         },
        //         "another_id": "attribute_id"
        //     }
        // })
        //     .to_string();
        // let (status_code, _) = response_from::<Value>(
        //     state.clone(),
        //     "/objects?attributes[attribute_id]=1",
        //     Method::PATCH,
        //     Body::new(body),
        // )
        //     .await;
        // assert_eq!(status_code, StatusCode::BAD_REQUEST);
        //
        // // Even if some of the attributes could update, the whole changeset should be rolled backed.
        // assert_correct_records(state.client(), entries, &[]).await;
        //
        // let body = json!({
        //     "attributes": {
        //         // A completely new attribute should successfully update.
        //         "another_id": "attribute_id"
        //     }
        // })
        // .to_string();
        // let (_, result) = response_from::<FileObject>(
        //     state.clone(),
        //     &format!("/objects/{}", first.object_id),
        //     Method::PATCH,
        //     Body::new(body.clone()),
        // )
        // .await;
        //
        // first.attributes.as_mut().unwrap()["another_id"] = json!("attribute_id");
        // assert_eq!(result, first);
        //
        // change_attributes(state.client(), &entries[1], &json!({
        //     "attribute_id": "1"
        // }).to_string()).await;
        //
        // let (status_code, _) = response_from::<Value>(
        //     state.clone(),
        //     "/objects?attributes[attribute_id]=1",
        //     Method::PATCH,
        //     Body::new(body),
        // )
        //     .await;
        // assert_eq!(status_code, StatusCode::BAD_REQUEST);
        //
        // // The state of the database should have the new attributes now.
        // let current_object = GetQueryBuilder::new(state.client())
        //     .get_object(first.object_id)
        //     .await
        //     .unwrap()
        //     .unwrap();
        // assert_eq!(current_object, first);
        //
        // assert_correct_records(state.client(), entries, first.object_id).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_object_attributes_api_insert_non_existent(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = initialize_database(state.client(), 10).await.objects;

        let mut first = entries[0].clone();
        let mut second = entries[1].clone();

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

        first.attributes.as_mut().unwrap()["another_id"] = json!("attribute_id");
        second.attributes.as_mut().unwrap()["another_id"] = json!("attribute_id");

        let (_, result) = response_from::<FileObject>(
            state.clone(),
            &format!(
                "/objects/{}?merge_strategy=InsertNonExistent",
                first.object_id
            ),
            Method::PATCH,
            Body::new(body.clone()),
        )
        .await;
        assert_eq!(result, first);
        let (_, result) = response_from::<Vec<FileObject>>(
            state.clone(),
            "/objects?merge_strategy=InsertNonExistent&attributes[attribute_id]=1",
            Method::PATCH,
            Body::new(body),
        )
        .await;
        assert_eq!(result, vec![second.clone()]);

        assert_correct_records(
            state.client(),
            entries,
            &[first.object_id, second.object_id],
        )
        .await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_object_attributes_api_replace(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = initialize_database(state.client(), 10).await.objects;

        let mut first = entries[0].clone();
        let mut second = entries[1].clone();

        let body = json!({
            "attributes": {
                // An existing attribute should overwrite.
                "attribute_id": {
                    "nested_id": "attribute_id"
                }
            }
        })
        .to_string();

        first.attributes.as_mut().unwrap()["attribute_id"] = json!({"nested_id": "attribute_id"});
        second.attributes.as_mut().unwrap()["attribute_id"] = json!({"nested_id": "attribute_id"});

        let (_, result) = response_from::<FileObject>(
            state.clone(),
            &format!("/objects/{}?merge_strategy=Replace", first.object_id),
            Method::PATCH,
            Body::new(body.clone()),
        )
        .await;
        assert_eq!(result, first);
        let (_, result) = response_from::<Vec<FileObject>>(
            state.clone(),
            "/objects?merge_strategy=Replace&attributes[attribute_id]=1",
            Method::PATCH,
            Body::new(body),
        )
        .await;
        assert_eq!(result, vec![second.clone()]);

        assert_correct_records(
            state.client(),
            entries,
            &[first.object_id, second.object_id],
        )
        .await;
    }
}
