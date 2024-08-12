use axum::extract::{Path, Query, State};
use axum::routing::patch;
use axum::{Json, Router};
use sea_orm::TransactionTrait;
use serde::Deserialize;
use serde_qs::axum::QsQuery;
use utoipa::ToSchema;
use uuid::Uuid;

use crate::database::entities::s3_object;
use crate::database::entities::s3_object::Model as FileS3Object;
use crate::error::Error::ExpectedSomeValue;
use crate::error::Result;
use crate::queries::update::UpdateQueryBuilder;
use crate::routes::error::ErrorStatusCode;
use crate::routes::filter::S3ObjectsFilter;
use crate::routes::list::{ListS3ObjectsParams, WildcardParams};
use crate::routes::AppState;

/// The attributes to update for the request. This updates attributes according to JSON patch.
/// See [JSON patch](https://jsonpatch.com/) and [RFC6902](https://datatracker.ietf.org/doc/html/rfc6902/).
///
/// In order to apply the patch, the outer type of the JSON input must have one key called "attributes".
/// Then any JSON patch operation can be used to update the attributes, e.g. "add" or "replace". The
/// "test" operation can be used to confirm whether a key is a specific value before updating. If the
/// check fails,  a `BAD_REQUEST` is returned and no records are updated.
#[derive(Debug, Deserialize, Default, Clone, ToSchema)]
#[schema(
    example = json!({
        "attributes": [
            { "op": "test", "path": "/attribute_id", "value": "1" },
            { "op": "replace", "path": "/attribute_id", "value": "attribute_id" }
        ]
    })
)]
pub struct PatchBody {
    /// The JSON patch for a record's attributes.
    attributes: Patch,
}

/// The JSON patch for attributes.
#[derive(Debug, Deserialize, Default, Clone, ToSchema)]
#[schema(value_type = Value)]
pub struct Patch(json_patch::Patch);

impl PatchBody {
    /// Create a new attribute body.
    pub fn new(attributes: Patch) -> Self {
        Self { attributes }
    }

    /// Get the inner map.
    pub fn into_inner(self) -> json_patch::Patch {
        self.attributes.0
    }

    /// Get the inner map as a reference
    pub fn get_ref(&self) -> &json_patch::Patch {
        &self.attributes.0
    }
}

/// Update the s3_object attributes using a JSON patch request.
#[utoipa::path(
    patch,
    path = "/s3_objects/{id}",
    responses(
        (
            status = OK,
            description = "The updated s3_object",
            body = FileS3Object
        ),
        ErrorStatusCode,
    ),
    request_body = PatchBody,
    context_path = "/api/v1",
    tag = "update",
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
        .ok_or_else(|| ExpectedSomeValue(id))?;

    txn.commit().await?;

    Ok(Json(results))
}

/// Update the attributes for a collection of s3_objects using a JSON patch request.
/// This updates all attributes matching the filter params with the same JSON patch.
#[utoipa::path(
    patch,
    path = "/s3_objects",
    responses(
        (
            status = OK,
            description = "The updated s3_objects",
            body = Vec<FileS3Object>
        ),
        ErrorStatusCode,
    ),
    params(WildcardParams, ListS3ObjectsParams, S3ObjectsFilter),
    request_body = PatchBody,
    context_path = "/api/v1",
    tag = "update",
)]
pub async fn update_s3_object_collection_attributes(
    state: State<AppState>,
    Query(wildcard): Query<WildcardParams>,
    Query(list): Query<ListS3ObjectsParams>,
    QsQuery(filter_all): QsQuery<S3ObjectsFilter>,
    Json(patch): Json<PatchBody>,
) -> Result<Json<Vec<FileS3Object>>> {
    let txn = state.client().connection_ref().begin().await?;

    let mut results = UpdateQueryBuilder::<_, s3_object::Entity>::new(&txn)
        .filter_all(filter_all, wildcard.case_sensitive());

    if list.current_state() {
        results = results.current_state();
    }

    let results = results
        .update_s3_object_attributes(patch)
        .await?
        .all()
        .await?;

    txn.commit().await?;

    Ok(Json(results))
}

/// The router for updating objects.
pub fn update_router() -> Router<AppState> {
    Router::new()
        .route("/s3_objects/:id", patch(update_s3_object_attributes))
        .route("/s3_objects", patch(update_s3_object_collection_attributes))
}

#[cfg(test)]
mod tests {
    use crate::queries::update::tests::{assert_contains, entries_many};
    use axum::body::Body;
    use axum::http::{Method, StatusCode};
    use serde_json::json;
    use sqlx::PgPool;

    use crate::database::aws::migration::tests::MIGRATOR;

    use super::*;
    use crate::queries::update::tests::{
        assert_correct_records, assert_model_contains, assert_wildcard_update,
        change_attribute_entries, change_attributes, change_many,
    };
    use crate::queries::EntriesBuilder;
    use crate::routes::list::tests::response_from;
    use crate::uuid::UuidGenerator;
    use serde_json::Value;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attribute_api_replace(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(state.client()).await;

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

        let (_, s3_object) = response_from::<FileS3Object>(
            state.clone(),
            &format!("/s3_objects/{}", entries.s3_objects[0].s3_object_id),
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;

        change_attribute_entries(&mut entries, 0, json!({"attribute_id": "attribute_id"}));

        assert_model_contains(&[s3_object], &entries.s3_objects, 0..1);
        assert_correct_records(state.client(), entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attribute_api_not_found(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(state.client()).await;

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

        let (s3_object_status_code, _) = response_from::<Value>(
            state.clone(),
            &format!("/s3_objects/{}", UuidGenerator::generate()),
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;
        assert_eq!(s3_object_status_code, StatusCode::NOT_FOUND);

        // Nothing is expected to change.
        change_attribute_entries(&mut entries, 0, json!({"attribute_id": "1"}));
        assert_correct_records(state.client(), entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_collection_attributes_api_replace(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(state.client()).await;

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

        let (_, s3_objects) = response_from::<Vec<FileS3Object>>(
            state.clone(),
            "/s3_objects?attributes[attribute_id]=1",
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;

        change_attribute_entries(&mut entries, 0, json!({"attribute_id": "attribute_id"}));
        change_attribute_entries(&mut entries, 1, json!({"attribute_id": "attribute_id"}));

        assert_model_contains(&s3_objects, &entries.s3_objects, 0..2);
        assert_correct_records(state.client(), entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_s3_attributes_current_state(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(state.client()).await;

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

        let (_, s3_objects) = response_from::<Vec<FileS3Object>>(
            state.clone(),
            "/s3_objects?current_state=true&attributes[attribute_id]=1",
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;

        // Only the created event should be updated.
        entries.s3_objects[0].attributes = Some(json!({"attribute_id": "attribute_id"}));
        entries.s3_objects[1].attributes = Some(json!({"attribute_id": "1"}));

        assert_model_contains(&s3_objects, &entries.s3_objects, 0..1);
        assert_correct_records(state.client(), entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_collection_attributes_api_no_op(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(state.client()).await;

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

        let (_, s3_objects) = response_from::<Vec<FileS3Object>>(
            state.clone(),
            "/s3_objects?attributes[attribute_id]=1",
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;
        assert!(s3_objects.is_empty());

        change_attribute_entries(&mut entries, 0, json!({"attribute_id": "2"}));
        change_attribute_entries(&mut entries, 1, json!({"attribute_id": "2"}));
        assert_correct_records(state.client(), entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_wildcard_like(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(state.client()).await;

        change_many(
            state.client(),
            &entries,
            &[0, 1],
            Some(json!({"attribute_id": "attribute_id"})),
        )
        .await;

        let patch = json!({"attributes": [
            { "op": "add", "path": "/another_attribute", "value": "1" },
        ]});

        entries_many(
            &mut entries,
            &[0, 1],
            json!({"attribute_id": "attribute_id", "another_attribute": "1"}),
        );

        let (_, s3_objects) = response_from::<Vec<FileS3Object>>(
            state.clone(),
            "/s3_objects?attributes[attribute_id]=%a%",
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;

        assert_contains(&s3_objects, &entries, 0..2);
        assert_correct_records(state.client(), entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_wildcard_ilike(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(state.client()).await;

        change_many(
            state.client(),
            &entries,
            &[0, 1],
            Some(json!({"attribute_id": "attribute_id"})),
        )
        .await;

        let patch = json!({"attributes": [
            { "op": "add", "path": "/another_attribute", "value": "1" },
        ]});

        entries_many(
            &mut entries,
            &[0, 1],
            json!({"attribute_id": "attribute_id", "another_attribute": "1"}),
        );

        let (_, s3_objects) = response_from::<Vec<FileS3Object>>(
            state.clone(),
            "/s3_objects?attributes[attribute_id]=%A%",
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;
        assert!(s3_objects.is_empty());

        let (_, s3_objects) = response_from::<Vec<FileS3Object>>(
            state.clone(),
            "/s3_objects?attributes[attribute_id]=%A%&case_sensitive=false",
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;

        assert_contains(&s3_objects, &entries, 0..2);
        assert_correct_records(state.client(), entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_api_wildcard_like(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(state.client()).await;

        change_many(
            state.client(),
            &entries,
            &[0, 2, 4, 6, 8],
            Some(json!({"attribute_id": "1"})),
        )
        .await;

        let patch = json!({"attributes": [
            { "op": "add", "path": "/another_attribute", "value": "1" },
        ]});

        let (_, s3_objects) = response_from::<Vec<FileS3Object>>(
            state.clone(),
            "/s3_objects?event_type=C__%",
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;

        assert_wildcard_update(&mut entries, &s3_objects);
        assert_correct_records(state.client(), entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_api_wildcard_ilike(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(state.client()).await;

        change_many(
            state.client(),
            &entries,
            &[0, 2, 4, 6, 8],
            Some(json!({"attribute_id": "1"})),
        )
        .await;

        let patch = json!({"attributes": [
            { "op": "add", "path": "/another_attribute", "value": "1" },
        ]});

        let (_, s3_objects) = response_from::<Vec<FileS3Object>>(
            state.clone(),
            // Percent-encoding should work too.
            "/s3_objects?case_sensitive=false&event_type=c%25_%25d",
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;

        assert_wildcard_update(&mut entries, &s3_objects);
        assert_correct_records(state.client(), entries).await;
    }
}
