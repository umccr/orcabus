use axum::extract::{Path, State};
use axum::Json;
use json_patch::Patch;
use sea_orm::TransactionTrait;
use serde::Deserialize;
use serde_qs::axum::QsQuery;
use uuid::Uuid;

use crate::database::entities::object::Model as FileObject;
use crate::database::entities::s3_object::Model as FileS3Object;
use crate::database::entities::{object, s3_object};
use crate::error::Error::APIError;
use crate::error::Result;
use crate::queries::update::UpdateQueryBuilder;
use crate::routes::filtering::{ObjectsFilterAll, S3ObjectsFilterAll};
use crate::routes::ErrorStatusCode::BadRequest;
use crate::routes::{AppState, ErrorResponse, ErrorStatusCode};

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
pub struct PatchBody {
    attributes: Patch,
}

impl PatchBody {
    /// Create a new attribute body.
    pub fn new(attributes: Patch) -> Self {
        Self { attributes }
    }

    /// Get the inner map.
    pub fn into_inner(self) -> Patch {
        self.attributes
    }

    /// Get the inner map as a reference
    pub fn get_ref(&self) -> &Patch {
        &self.attributes
    }
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
    request_body = PatchBody,
    context_path = "/api/v1",
)]
pub async fn update_object_attributes(
    state: State<AppState>,
    Path(id): Path<Uuid>,
    Json(patch): Json<PatchBody>,
) -> Result<Json<FileObject>> {
    let txn = state.client().connection_ref().begin().await?;

    let results = UpdateQueryBuilder::<_, object::Entity>::new(&txn)
        .for_id(id)
        .update_object_attributes(patch)
        .await?
        .one()
        .await?
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
    params(ObjectsFilterAll),
    request_body = PatchBody,
    context_path = "/api/v1",
)]
pub async fn update_object_collection_attributes(
    state: State<AppState>,
    QsQuery(filter_all): QsQuery<ObjectsFilterAll>,
    Json(patch): Json<PatchBody>,
) -> Result<Json<Vec<FileObject>>> {
    let txn = state.client().connection_ref().begin().await?;

    let results = UpdateQueryBuilder::<_, object::Entity>::new(&txn)
        .filter_all(filter_all)
        .update_object_attributes(patch)
        .await?
        .all()
        .await?;

    txn.commit().await?;

    Ok(Json(results))
}

/// Update the s3_object attributes using a patch request.
#[utoipa::path(
    patch,
    path = "/s3_objects/{id}",
    responses(
        (
            status = OK,
            description = "Update a single s3_object's attributes and return the updated object",
            body = FileS3Object
        ),
        ErrorStatusCode,
    ),
    request_body = PatchBody,
    context_path = "/api/v1",
)]
pub async fn update_s3_object_attributes(
    state: State<AppState>,
    Path(id): Path<Uuid>,
    Json(patch): Json<PatchBody>,
) -> Result<Json<FileS3Object>> {
    let txn = state.client().connection_ref().begin().await?;

    let results = UpdateQueryBuilder::<_, s3_object::Entity>::new(&txn)
        .for_id(id)
        .update_s3_object_attributes(patch)
        .await?
        .one()
        .await?
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
    path = "/s3_objects",
    responses(
        (
        status = OK,
        description = "Update attributes for a collection of s3_object and return the updated objects",
        body = Vec<FileS3Object>
        ),
        ErrorStatusCode,
    ),
    params(ObjectsFilterAll),
    request_body = PatchBody,
    context_path = "/api/v1",
)]
pub async fn update_s3_object_collection_attributes(
    state: State<AppState>,
    QsQuery(filter_all): QsQuery<S3ObjectsFilterAll>,
    Json(patch): Json<PatchBody>,
) -> Result<Json<Vec<FileS3Object>>> {
    let txn = state.client().connection_ref().begin().await?;

    let results = UpdateQueryBuilder::<_, s3_object::Entity>::new(&txn)
        .filter_all(filter_all)
        .update_s3_object_attributes(patch)
        .await?
        .all()
        .await?;

    txn.commit().await?;

    Ok(Json(results))
}

#[cfg(test)]
mod tests {
    use axum::body::Body;
    use axum::http::{Method, StatusCode};
    use serde_json::json;
    use sqlx::PgPool;

    use crate::database::aws::migration::tests::MIGRATOR;

    use crate::queries::tests::initialize_database;
    use crate::queries::update::tests::{
        assert_correct_records, assert_model_contains, change_attribute_entries, change_attributes,
    };
    use crate::routes::list::tests::response_from;
    use crate::uuid::UuidGenerator;
    use serde_json::Value;

    use super::*;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attribute_api_replace(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let mut entries = initialize_database(state.client(), 10).await;

        change_attributes(
            state.client(),
            &entries,
            0,
            Some(json!({"attribute_id": "1"})),
        )
        .await;

        let patch = json!({"attributes": [
            { "op": "test", "path": "/attribute_id", "value": "1" },
            { "op": "replace", "path": "/attribute_id", "value": "attribute_id" },
        ]});

        let (_, object) = response_from::<FileObject>(
            state.clone(),
            &format!("/objects/{}", entries.objects[0].object_id),
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;
        let (_, s3_object) = response_from::<FileS3Object>(
            state.clone(),
            &format!("/s3_objects/{}", entries.s3_objects[0].s3_object_id),
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;

        change_attribute_entries(&mut entries, 0, json!({"attribute_id": "attribute_id"})).await;

        assert_model_contains(&[object], &entries.objects, 0..1);
        assert_model_contains(&[s3_object], &entries.s3_objects, 0..1);
        assert_correct_records(state.client(), entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attribute_api_err(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let mut entries = initialize_database(state.client(), 10).await;

        change_attributes(
            state.client(),
            &entries,
            0,
            Some(json!({"attribute_id": "1"})),
        )
        .await;

        let patch = json!({"attributes": [
            { "op": "test", "path": "/attribute_id", "value": "1" },
            { "op": "replace", "path": "/attribute_id", "value": "attribute_id" },
        ]});

        let (object_status_code, _) = response_from::<Value>(
            state.clone(),
            &format!("/objects/{}", UuidGenerator::generate()),
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;
        let (s3_object_status_code, _) = response_from::<Value>(
            state.clone(),
            &format!("/s3_objects/{}", UuidGenerator::generate()),
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;

        assert_eq!(object_status_code, StatusCode::BAD_REQUEST);
        assert_eq!(s3_object_status_code, StatusCode::BAD_REQUEST);

        // Nothing is expected to change.
        change_attribute_entries(&mut entries, 0, json!({"attribute_id": "1"})).await;
        assert_correct_records(state.client(), entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_collection_attributes_api_replace(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let mut entries = initialize_database(state.client(), 10).await;

        change_attributes(
            state.client(),
            &entries,
            0,
            Some(json!({"attribute_id": "1"})),
        )
        .await;
        change_attributes(
            state.client(),
            &entries,
            1,
            Some(json!({"attribute_id": "1"})),
        )
        .await;

        let patch = json!({"attributes": [
            { "op": "test", "path": "/attribute_id", "value": "1" },
            { "op": "replace", "path": "/attribute_id", "value": "attribute_id" },
        ]});

        let (_, objects) = response_from::<Vec<FileObject>>(
            state.clone(),
            "/objects?attributes[attribute_id]=1",
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;
        let (_, s3_objects) = response_from::<Vec<FileS3Object>>(
            state.clone(),
            "/s3_objects?attributes[attribute_id]=1",
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;

        change_attribute_entries(&mut entries, 0, json!({"attribute_id": "attribute_id"})).await;
        change_attribute_entries(&mut entries, 1, json!({"attribute_id": "attribute_id"})).await;

        assert_model_contains(&objects, &entries.objects, 0..2);
        assert_model_contains(&s3_objects, &entries.s3_objects, 0..2);
        assert_correct_records(state.client(), entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_collection_attributes_api_no_op(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let mut entries = initialize_database(state.client(), 10).await;

        change_attributes(
            state.client(),
            &entries,
            0,
            Some(json!({"attribute_id": "2"})),
        )
        .await;
        change_attributes(
            state.client(),
            &entries,
            1,
            Some(json!({"attribute_id": "2"})),
        )
        .await;

        let patch = json!({"attributes": [
            { "op": "remove", "path": "/attribute_id" },
        ]});

        let (_, objects) = response_from::<Vec<FileObject>>(
            state.clone(),
            "/objects?attributes[attribute_id]=1",
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;
        let (_, s3_objects) = response_from::<Vec<FileS3Object>>(
            state.clone(),
            "/s3_objects?attributes[attribute_id]=1",
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;

        assert!(objects.is_empty());
        assert!(s3_objects.is_empty());

        change_attribute_entries(&mut entries, 0, json!({"attribute_id": "2"})).await;
        change_attribute_entries(&mut entries, 1, json!({"attribute_id": "2"})).await;
        assert_correct_records(state.client(), entries).await;
    }
}
