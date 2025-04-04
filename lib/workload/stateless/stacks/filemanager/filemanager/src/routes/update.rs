use axum::extract::State;
use axum::routing::patch;
use axum::{extract, Router};
use axum_extra::extract::WithRejection;
use sea_orm::TransactionTrait;
use serde::Deserialize;
use utoipa::ToSchema;
use uuid::Uuid;

use crate::database::entities::s3_object;
use crate::database::entities::s3_object::Model as S3;
use crate::error::Error::ExpectedSomeValue;
use crate::error::Result;
use crate::queries::update::UpdateQueryBuilder;
use crate::routes::error::{ErrorStatusCode, Json, Path, QsQuery, Query};
use crate::routes::filter::S3ObjectsFilter;
use crate::routes::list::{ListS3Params, WildcardParams};
use crate::routes::AppState;

/// The attributes to update for the request. This updates attributes according to JSON patch.
/// See [JSON patch](https://jsonpatch.com/) and [RFC6902](https://datatracker.ietf.org/doc/html/rfc6902/).
///
/// In order to apply the patch, JSON body must contain an array with patch operations. The patch operations
/// are append-only, which means that only "add" and "test" is supported. If a "test" check fails,
/// a patch operations that isn't "add" or "test" is used, or if a key already exists, a `BAD_REQUEST`
/// is returned and no records are updated. Use `attributes` to update attributes and `ingestId` to
/// update the ingest id.
#[derive(Debug, Deserialize, Clone, ToSchema)]
#[serde(untagged)]
#[schema(
    examples(
        json!([
            { "op": "add", "path": "/attributeId", "value": "attributeId" }
        ]),
        json!({
            "attributes": [
                { "op": "add", "path": "/attributeId", "value": "attributeId" }
            ]
        }),
        json!({
            "ingestId": [
                { "op": "add", "path": "/", "value": "00000000-0000-0000-0000-000000000000" }
            ]
        })
    )
)]
pub enum PatchBody {
    NestedAttributes {
        /// The JSON patch for a record's attributes.
        attributes: Patch,
    },
    NestedIngestId {
        /// The JSON patch for a record's ingest_id. Only `add` with a `/` path is supported.
        #[serde(rename = "ingestId")]
        ingest_id: Patch,
    },
    UnnestedAttributes(Patch),
}

/// The JSON patch for attributes.
#[derive(Debug, Deserialize, Default, Clone, ToSchema)]
#[serde(rename_all = "camelCase")]
#[schema(value_type = Value)]
pub struct Patch(json_patch::Patch);

impl Patch {
    /// Create a new patch.
    pub fn new(patch: json_patch::Patch) -> Self {
        Self(patch)
    }

    /// Get the inner patch.
    pub fn into_inner(self) -> json_patch::Patch {
        self.0
    }
}

impl PatchBody {
    /// Create a new attribute body.
    pub fn new(attributes: Patch) -> Self {
        Self::UnnestedAttributes(attributes)
    }

    /// Get the inner map.
    pub fn into_inner(self) -> json_patch::Patch {
        match self {
            PatchBody::NestedAttributes { attributes } => attributes.0,
            PatchBody::NestedIngestId { ingest_id } => ingest_id.0,
            PatchBody::UnnestedAttributes(attributes) => attributes.0,
        }
    }

    /// Get the inner map as a reference
    pub fn get_ref(&self) -> &json_patch::Patch {
        match self {
            PatchBody::NestedAttributes { attributes } => &attributes.0,
            PatchBody::NestedIngestId { ingest_id } => &ingest_id.0,
            PatchBody::UnnestedAttributes(attributes) => &attributes.0,
        }
    }
}

/// Update the s3_object attributes using a JSON patch request.
#[utoipa::path(
    patch,
    path = "/s3/{id}",
    responses(
        (
            status = OK,
            description = "The updated s3_object",
            body = S3
        ),
        ErrorStatusCode,
    ),
    request_body = PatchBody,
    context_path = "/api/v1",
    tag = "update",
)]
pub async fn update_s3_attributes(
    state: State<AppState>,
    WithRejection(extract::Path(id), _): Path<Uuid>,
    WithRejection(extract::Json(patch), _): Json<PatchBody>,
) -> Result<extract::Json<S3>> {
    let txn = state.database_client().connection_ref().begin().await?;

    let results = UpdateQueryBuilder::<_, s3_object::Entity>::new(&txn)
        .for_id(id)
        .update_s3_attributes(patch)
        .await?
        .one()
        .await?
        .ok_or_else(|| ExpectedSomeValue(id))?;

    txn.commit().await?;

    Ok(extract::Json(results))
}

/// Update the attributes for a collection of s3_objects using a JSON patch request.
/// This updates all attributes matching the filter params with the same JSON patch.
#[utoipa::path(
    patch,
    path = "/s3",
    responses(
        (
            status = OK,
            description = "The updated s3_objects",
            body = Vec<S3>
        ),
        ErrorStatusCode,
    ),
    params(WildcardParams, ListS3Params, S3ObjectsFilter),
    request_body = PatchBody,
    context_path = "/api/v1",
    tag = "update",
)]
pub async fn update_s3_collection_attributes(
    state: State<AppState>,
    WithRejection(extract::Query(wildcard), _): Query<WildcardParams>,
    WithRejection(extract::Query(list), _): Query<ListS3Params>,
    WithRejection(serde_qs::axum::QsQuery(filter_all), _): QsQuery<S3ObjectsFilter>,
    WithRejection(extract::Json(patch), _): Json<PatchBody>,
) -> Result<extract::Json<Vec<S3>>> {
    let txn = state.database_client().connection_ref().begin().await?;

    let results = UpdateQueryBuilder::<_, s3_object::Entity>::new(&txn).filter_all(
        filter_all,
        wildcard.case_sensitive(),
        list.current_state(),
    )?;

    let results = results.update_s3_attributes(patch).await?.all().await?;

    txn.commit().await?;

    Ok(extract::Json(results))
}

/// The router for updating objects.
pub fn update_router() -> Router<AppState> {
    Router::new()
        .route("/s3/{id}", patch(update_s3_attributes))
        .route("/s3", patch(update_s3_collection_attributes))
}

#[cfg(test)]
mod tests {
    use axum::body::Body;
    use axum::http::{Method, StatusCode};
    use serde_json::json;
    use serde_json::Value;
    use sqlx::PgPool;

    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::queries::update::tests::{assert_contains, entries_many};
    use crate::queries::update::tests::{
        assert_correct_records, assert_model_contains, assert_wildcard_update,
        change_attribute_entries, change_attributes, change_many, update_ingest_ids,
    };
    use crate::queries::EntriesBuilder;
    use crate::routes::list::tests::response_from;
    use crate::uuid::UuidGenerator;

    use super::*;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attribute_api_unsupported(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let mut entries = EntriesBuilder::default()
            .build(state.database_client())
            .await
            .unwrap();

        change_attributes(
            state.database_client(),
            &entries,
            0,
            Some(json!({"attributeId": "1"})),
        )
        .await;

        let patch = json!([
            { "op": "test", "path": "/attributeId", "value": "1" },
            { "op": "replace", "path": "/attributeId", "value": "attributeId" },
        ]);

        let (status, _) = response_from::<Value>(
            state.clone(),
            &format!("/s3/{}", entries.s3_objects[0].s3_object_id),
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;
        assert_eq!(status, StatusCode::BAD_REQUEST);

        change_attribute_entries(&mut entries, 0, json!({"attributeId": "1"}));
        assert_correct_records(state.database_client(), entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attribute_api_not_found(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let mut entries = EntriesBuilder::default()
            .build(state.database_client())
            .await
            .unwrap();

        change_attributes(
            state.database_client(),
            &entries,
            0,
            Some(json!({"attributeId": "1"})),
        )
        .await;

        let patch = json!({"attributes": [
            { "op": "test", "path": "/attributeId", "value": "1" },
            { "op": "add", "path": "/anotherAttribute", "value": "anotherAttribute" },
        ]});

        let (s3_object_status_code, _) = response_from::<Value>(
            state.clone(),
            &format!("/s3/{}", UuidGenerator::generate()),
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;
        assert_eq!(s3_object_status_code, StatusCode::NOT_FOUND);

        // Nothing is expected to change.
        change_attribute_entries(&mut entries, 0, json!({"attributeId": "1"}));
        assert_correct_records(state.database_client(), entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_collection_attributes_api_add_nested(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let mut entries = EntriesBuilder::default()
            .build(state.database_client())
            .await
            .unwrap();

        change_attributes(
            state.database_client(),
            &entries,
            0,
            Some(json!({"attributeId": "1"})),
        )
        .await;
        change_attributes(
            state.database_client(),
            &entries,
            1,
            Some(json!({"attributeId": "1"})),
        )
        .await;

        let patch = json!({"attributes": [
            { "op": "test", "path": "/attributeId", "value": "1" },
            { "op": "add", "path": "/anotherAttribute", "value": "anotherAttribute" },
        ]});

        let (_, s3_objects) = response_from::<Vec<S3>>(
            state.clone(),
            "/s3?currentState=false&attributes[attributeId]=1",
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;

        change_attribute_entries(
            &mut entries,
            0,
            json!({"attributeId": "1", "anotherAttribute": "anotherAttribute"}),
        );
        change_attribute_entries(
            &mut entries,
            1,
            json!({"attributeId": "1", "anotherAttribute": "anotherAttribute"}),
        );

        assert_model_contains(&s3_objects, &entries.s3_objects, 0..2);
        assert_correct_records(state.database_client(), entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_collection_attributes_api(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let mut entries = EntriesBuilder::default()
            .build(state.database_client())
            .await
            .unwrap();

        change_attributes(
            state.database_client(),
            &entries,
            0,
            Some(json!({"attributeId": "1"})),
        )
        .await;
        change_attributes(
            state.database_client(),
            &entries,
            1,
            Some(json!({"attributeId": "1"})),
        )
        .await;

        let patch = json!([
            { "op": "test", "path": "/attributeId", "value": "1" },
            { "op": "add", "path": "/anotherAttribute", "value": "anotherAttribute" },
        ]);

        let (_, s3_objects) = response_from::<Vec<S3>>(
            state.clone(),
            "/s3?currentState=false&attributes[attributeId]=1",
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;

        change_attribute_entries(
            &mut entries,
            0,
            json!({"attributeId": "1", "anotherAttribute": "anotherAttribute"}),
        );
        change_attribute_entries(
            &mut entries,
            1,
            json!({"attributeId": "1", "anotherAttribute": "anotherAttribute"}),
        );

        assert_model_contains(&s3_objects, &entries.s3_objects, 0..2);
        assert_correct_records(state.database_client(), entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_s3_attributes_current_state(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let mut entries = EntriesBuilder::default()
            .build(state.database_client())
            .await
            .unwrap();

        change_attributes(
            state.database_client(),
            &entries,
            0,
            Some(json!({"attributeId": "1"})),
        )
        .await;
        change_attributes(
            state.database_client(),
            &entries,
            1,
            Some(json!({"attributeId": "1"})),
        )
        .await;

        let patch = json!({"attributes": [
            { "op": "test", "path": "/attributeId", "value": "1" },
            { "op": "add", "path": "/anotherAttribute", "value": "1" },
        ]});

        let (_, s3_objects) = response_from::<Vec<S3>>(
            state.clone(),
            "/s3?attributes[attributeId]=1",
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;

        // Only the created event should be updated.
        entries.s3_objects[0].attributes =
            Some(json!({"attributeId": "1", "anotherAttribute": "1"}));
        entries.s3_objects[1].attributes = Some(json!({"attributeId": "1"}));

        assert_model_contains(&s3_objects, &entries.s3_objects, 0..1);
        assert_correct_records(state.database_client(), entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_ingest_id(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let client = state.database_client();
        let mut entries = EntriesBuilder::default().build(client).await.unwrap();

        let patch = json!({
            "ingestId": [
                { "op": "add", "path": "/", "value": "00000000-0000-0000-0000-000000000000" },
            ]
        });

        change_many(client, &entries, &[0, 1], Some(json!({"attributeId": "1"}))).await;
        update_ingest_ids(client, &mut entries).await;

        let (_, s3_objects) = response_from::<Vec<S3>>(
            state.clone(),
            "/s3?attributes[attributeId]=1&currentState=false",
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;

        entries_many(&mut entries, &[0, 1], json!({"attributeId": "1"}));
        entries.s3_objects[0].ingest_id = Some(Uuid::default());
        entries.s3_objects[1].ingest_id = Some(Uuid::default());

        assert_contains(&s3_objects, &entries, 0..2);
        assert_correct_records(client, entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_ingest_id_single(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let client = state.database_client();
        let mut entries = EntriesBuilder::default().build(client).await.unwrap();

        change_many(client, &entries, &[0, 1], Some(json!({"attributeId": "1"}))).await;
        update_ingest_ids(client, &mut entries).await;

        let patch = json!({
            "ingestId": [
                { "op": "add", "path": "/", "value": "00000000-0000-0000-0000-000000000000" },
            ]
        });

        let (_, s3_objects) = response_from::<S3>(
            state.clone(),
            &format!("/s3/{}", entries.s3_objects[0].s3_object_id),
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;

        entries_many(&mut entries, &[0, 1], json!({"attributeId": "1"}));
        entries.s3_objects[0].ingest_id = Some(Uuid::default());
        entries.s3_objects[1].ingest_id = None;

        assert_contains(&vec![s3_objects], &entries, 0..1);
        assert_correct_records(client, entries.clone()).await;

        let patch = json!({
            "ingestId": [
                { "op": "replace", "path": "/", "value": "00000000-0000-0000-0000-000000000001" },
            ]
        });

        let (_, s3_objects) = response_from::<S3>(
            state.clone(),
            &format!("/s3/{}", entries.s3_objects[0].s3_object_id),
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;

        entries_many(&mut entries, &[0, 1], json!({"attributeId": "1"}));
        entries.s3_objects[0].ingest_id =
            Some("00000000-0000-0000-0000-000000000001".parse().unwrap());
        entries.s3_objects[1].ingest_id = None;

        assert_contains(&vec![s3_objects], &entries, 0..1);
        assert_correct_records(client, entries.clone()).await;

        let patch = json!({
            "ingestId": [
                { "op": "remove", "path": "/" },
            ]
        });

        let (_, s3_objects) = response_from::<S3>(
            state.clone(),
            &format!("/s3/{}", entries.s3_objects[0].s3_object_id),
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;

        entries_many(&mut entries, &[0, 1], json!({"attributeId": "1"}));
        entries.s3_objects[0].ingest_id = None;
        entries.s3_objects[1].ingest_id = None;

        assert_contains(&vec![s3_objects], &entries, 0..1);
        assert_correct_records(client, entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_ingest_id_error(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let client = state.database_client();
        let mut entries = EntriesBuilder::default().build(client).await.unwrap();

        change_many(client, &entries, &[0, 1], Some(json!({"attributeId": "1"}))).await;

        update_ingest_ids(client, &mut entries).await;

        let patch = json!({
            "ingestId": [
                { "op": "add", "path": "/", "value": "00000000-0000-0000-0000-00000000000" },
            ]
        });
        assert_ingest_id_error(state.clone(), patch).await;

        let patch = json!({
            "ingestId": [
                { "op": "add", "path": "/ingestId", "value": "00000000-0000-0000-0000-000000000000" },
            ]
        });
        assert_ingest_id_error(state.clone(), patch).await;

        let patch = json!({
            "ingestId": [
                { "op": "test", "path": "/", "value": "00000000-0000-0000-0000-00000000000" },
            ]
        });
        assert_ingest_id_error(state.clone(), patch).await;

        let patch = json!({
            "ingestId": [
                { "op": "add", "path": "/", "value": "00000000-0000-0000-0000-00000000000" },
                { "op": "add", "path": "/", "value": "00000000-0000-0000-0000-00000000000" },
            ]
        });
        assert_ingest_id_error(state, patch).await;
    }

    async fn assert_ingest_id_error(state: AppState, patch: Value) {
        let (code, _) = response_from::<Value>(
            state,
            "/s3?attributes[attributeId]=1&currentState=false",
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;
        assert!(code.is_client_error() || code.is_server_error());
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_collection_attributes_api_no_op(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let mut entries = EntriesBuilder::default()
            .build(state.database_client())
            .await
            .unwrap();

        change_attributes(
            state.database_client(),
            &entries,
            0,
            Some(json!({"attributeId": "2"})),
        )
        .await;
        change_attributes(
            state.database_client(),
            &entries,
            1,
            Some(json!({"attributeId": "2"})),
        )
        .await;

        let patch = json!({"attributes": [
            { "op": "add", "path": "/anotherAttribute", "value": "1" },
        ]});

        let (_, s3_objects) = response_from::<Vec<S3>>(
            state.clone(),
            "/s3?currentState=false&attributes[attributeId]=1",
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;
        assert!(s3_objects.is_empty());

        change_attribute_entries(&mut entries, 0, json!({"attributeId": "2"}));
        change_attribute_entries(&mut entries, 1, json!({"attributeId": "2"}));
        assert_correct_records(state.database_client(), entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_wildcard_like(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let mut entries = EntriesBuilder::default()
            .build(state.database_client())
            .await
            .unwrap();

        change_many(
            state.database_client(),
            &entries,
            &[0, 1],
            Some(json!({"attributeId": "attributeId"})),
        )
        .await;

        let patch = json!({"attributes": [
            { "op": "add", "path": "/anotherAttribute", "value": "1" },
        ]});

        entries_many(
            &mut entries,
            &[0, 1],
            json!({"attributeId": "attributeId", "anotherAttribute": "1"}),
        );

        let (_, s3_objects) = response_from::<Vec<S3>>(
            state.clone(),
            "/s3?currentState=false&attributes[attributeId]=*a*",
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;

        assert_contains(&s3_objects, &entries, 0..2);
        assert_correct_records(state.database_client(), entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_wildcard_ilike(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let mut entries = EntriesBuilder::default()
            .build(state.database_client())
            .await
            .unwrap();

        change_many(
            state.database_client(),
            &entries,
            &[0, 1],
            Some(json!({"attributeId": "attributeId"})),
        )
        .await;

        let patch = json!({"attributes": [
            { "op": "add", "path": "/anotherAttribute", "value": "1" },
        ]});

        entries_many(
            &mut entries,
            &[0, 1],
            json!({"attributeId": "attributeId", "anotherAttribute": "1"}),
        );

        let (_, s3_objects) = response_from::<Vec<S3>>(
            state.clone(),
            "/s3?currentState=false&attributes[attributeId]=*A*",
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;
        assert!(s3_objects.is_empty());

        let (_, s3_objects) = response_from::<Vec<S3>>(
            state.clone(),
            "/s3?currentState=false&attributes[attributeId]=*A*&caseSensitive=false",
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;

        assert_contains(&s3_objects, &entries, 0..2);
        assert_correct_records(state.database_client(), entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_api_wildcard_like(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let mut entries = EntriesBuilder::default()
            .build(state.database_client())
            .await
            .unwrap();

        change_many(
            state.database_client(),
            &entries,
            &[0, 2, 4, 6, 8],
            Some(json!({"attributeId": "1"})),
        )
        .await;

        let patch = json!({"attributes": [
            { "op": "add", "path": "/anotherAttribute", "value": "1" },
        ]});

        let (_, s3_objects) = response_from::<Vec<S3>>(
            state.clone(),
            "/s3?eventTime=1970-01-0*",
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;

        assert_wildcard_update(&mut entries, &s3_objects);
        assert_correct_records(state.database_client(), entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_api_wildcard_ilike(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let mut entries = EntriesBuilder::default()
            .build(state.database_client())
            .await
            .unwrap();

        change_many(
            state.database_client(),
            &entries,
            &[0, 2, 4, 6, 8],
            Some(json!({"attributeId": "1"})),
        )
        .await;

        let patch = json!({"attributes": [
            { "op": "add", "path": "/anotherAttribute", "value": "1" },
        ]});

        let (_, s3_objects) = response_from::<Vec<S3>>(
            state.clone(),
            // Percent-encoding should work too.
            "/s3?caseSensitive=false&eventTime=1970-01-?%2A",
            Method::PATCH,
            Body::new(patch.to_string()),
        )
        .await;

        assert_wildcard_update(&mut entries, &s3_objects);
        assert_correct_records(state.database_client(), entries).await;
    }
}
