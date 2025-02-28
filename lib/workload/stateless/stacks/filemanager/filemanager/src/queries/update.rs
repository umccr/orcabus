//! Query builder to handle updating record columns.
//!

use json_patch::{patch, PatchOperation};
use sea_orm::prelude::{Expr, Json};
use sea_orm::sea_query::{
    Alias, Asterisk, CommonTableExpression, Query, SelectStatement, SimpleExpr, WithClause,
    WithQuery,
};
use sea_orm::{
    ColumnTrait, ConnectionTrait, EntityTrait, FromQueryResult, Iden, Iterable, ModelTrait,
    QueryFilter, QueryTrait, StatementBuilder, Value,
};
use serde_json::json;
use std::str::FromStr;
use uuid::Uuid;

use crate::database::entities::s3_object;
use crate::error::Error::{InvalidQuery, QueryError};
use crate::error::{Error, Result};
use crate::queries::list::ListQueryBuilder;
use crate::routes::filter::S3ObjectsFilter;
use crate::routes::update::PatchBody;

/// A query builder for list operations.
#[derive(Debug, Clone)]
pub struct UpdateQueryBuilder<'a, C, E>
where
    E: EntityTrait,
{
    connection: &'a C,
    select_to_update: ListQueryBuilder<'a, C, E>,
    // With query will eventually end up as the update
    update: WithQuery,
}

impl<'a, C> UpdateQueryBuilder<'a, C, s3_object::Entity>
where
    C: ConnectionTrait,
{
    /// Create a new query builder.
    pub fn new(connection: &'a C) -> Self {
        Self {
            connection,
            select_to_update: ListQueryBuilder::<_, s3_object::Entity>::new(connection),
            update: WithQuery::new(),
        }
    }

    /// Update the attributes on an object replacing any existing keys in the attributes.
    pub fn for_id(mut self, id: Uuid) -> Self {
        let (connection, mut select) = self.select_to_update.into_inner();

        select = select.filter(s3_object::Column::S3ObjectId.eq(id));

        self.select_to_update = (connection, select).into();
        self
    }

    /// Filter records by all fields in the filter variable.
    pub fn filter_all(
        mut self,
        filter: S3ObjectsFilter,
        case_sensitive: bool,
        current_state: bool,
    ) -> Result<Self> {
        self.select_to_update =
            self.select_to_update
                .filter_all(filter, case_sensitive, current_state)?;

        self.trace_query("filter_all");

        Ok(self)
    }

    /// Update the attributes on an s3_object using the attribute patch.
    pub async fn update_s3_attributes(self, patch: PatchBody) -> Result<Self> {
        let col = match patch {
            PatchBody::NestedIngestId { .. } => s3_object::Column::IngestId,
            _ => s3_object::Column::Attributes,
        };

        self.update_attributes(patch, s3_object::Column::S3ObjectId, col)
            .await
    }
}

impl<'a, C, E> From<(&'a C, ListQueryBuilder<'a, C, E>, WithQuery)> for UpdateQueryBuilder<'a, C, E>
where
    C: ConnectionTrait,
    E: EntityTrait,
{
    fn from(
        (connection, select_to_update, update): (&'a C, ListQueryBuilder<'a, C, E>, WithQuery),
    ) -> Self {
        Self {
            connection,
            select_to_update,
            update,
        }
    }
}

impl<'a, C, E> UpdateQueryBuilder<'a, C, E>
where
    C: ConnectionTrait,
    E: EntityTrait,
{
    /// Get the inner connection, with query and list query builder.
    pub fn into_inner(self) -> (&'a C, ListQueryBuilder<'a, C, E>, WithQuery) {
        (self.connection, self.select_to_update, self.update)
    }
}

impl<C, E, M> UpdateQueryBuilder<'_, C, E>
where
    C: ConnectionTrait,
    E: EntityTrait<Model = M>,
    M: ModelTrait + FromQueryResult + Send + Sync,
{
    /// Execute the prepared query, returning all values.
    pub async fn all(self) -> Result<Vec<M>> {
        // If there is nothing to update, just return an empty list.
        if self.update == WithQuery::new() {
            return Ok(vec![]);
        }

        let builder = self.connection.get_database_backend();
        let statement = StatementBuilder::build(&self.update, &builder);

        Ok(E::Model::find_by_statement(statement)
            .all(self.connection)
            .await?)
    }

    /// Execute the prepared query, returning one value.
    pub async fn one(self) -> Result<Option<M>> {
        Ok(self.all().await?.into_iter().nth(0))
    }

    /// Verifies that the JSON patch operation is supported.
    fn verify_patch(
        patch: Vec<PatchOperation>,
        current_attributes: &serde_json::Value,
    ) -> Result<Vec<PatchOperation>> {
        let check_exists = |path: String, patch: PatchOperation| {
            let exists = current_attributes.pointer(&path);
            if exists.is_some() {
                Err(InvalidQuery("path already exists".to_string()))
            } else {
                Ok(patch)
            }
        };

        patch
            .into_iter()
            .map(|patch| match patch {
                PatchOperation::Test(_) => Ok(patch),
                PatchOperation::Add(ref op) => check_exists(op.path.to_string(), patch),
                PatchOperation::Copy(ref op) => check_exists(op.path.to_string(), patch),
                _ => Err(InvalidQuery("unsupported JSON patch operation".to_string())),
            })
            .collect::<Result<Vec<_>>>()
    }

    /// Create an update for the attributes column.
    fn patch_for_attributes(
        patch_body: Vec<PatchOperation>,
        update_col: <<M as ModelTrait>::Entity as EntityTrait>::Column,
        model: M,
    ) -> Result<Value> {
        let mut current = if let Value::Json(json) = model.get(update_col) {
            let mut json = json.unwrap_or_else(|| Box::new(json!({})));
            if let &Json::Null = json.as_ref() {
                json = Box::new(json!({}));
            }
            json
        } else {
            return Err(QueryError("expected JSON attribute column".to_string()));
        };

        // Only append-style patching is supported.
        let operations = Self::verify_patch(patch_body, &current)?;

        // Patch it based on JSON patch.
        patch(&mut current, operations.as_slice()).map_err(|err| {
            InvalidQuery(format!(
                "JSON patch {} operation for {} path failed: {}",
                err.operation, err.path, err.kind
            ))
        })?;

        Ok(Value::Json(Some(current)))
    }

    /// Create an update for the ingestId column.
    fn patch_for_ingest_id(patch_body: Vec<PatchOperation>) -> Result<Value> {
        if patch_body.len() != 1 {
            return Err(QueryError(
                "expected one patch operation for `ingestId` update".to_string(),
            ));
        }
        if patch_body[0].path() != "/" {
            return Err(QueryError(
                "expected `/` path for `ingestId` update".to_string(),
            ));
        }

        let parse_uuid = |value: &serde_json::Value| {
            let uuid = Uuid::from_str(value.as_str().ok_or_else(|| {
                QueryError("expected string value for `ingestId` update".to_string())
            })?)
            .map_err(|err| {
                QueryError(format!(
                    "failed to parse UUID for `ingestId` update: {}",
                    err
                ))
            })?;

            Ok::<_, Error>(Value::Uuid(Some(Box::new(uuid))))
        };

        let to_update = match &patch_body[0] {
            PatchOperation::Add(add) => parse_uuid(&add.value)?,
            PatchOperation::Remove(_) => Value::Uuid(None),
            PatchOperation::Replace(replace) => parse_uuid(&replace.value)?,
            _ => {
                return Err(QueryError(
                    "expected `add`, `remove` or `replace` operation for `ingestId` update"
                        .to_string(),
                ))
            }
        };

        Ok(to_update)
    }

    /// Update the attributes on an object using the attribute patch. This first queries the
    /// required records to update using a previously specified select query in functions like
    /// `Self::for_id` and `Self::filter_all`. It then applies a JSON patch to the attributes of
    /// the records and updates them. The update statement generated is similar to:
    ///
    /// ```sql
    /// with update_with (id, attributes) as (select * from (values
    ///     (<uuid>, <current_attributes>),
    ///     ...
    /// ) AS values)
    /// update <s3_object> set attributes = (
    ///     select attributes from update_with where object_id = id
    /// ) where object_id in (select id from update_with)
    /// returning <updated_objects>
    /// ```
    pub async fn update_attributes(
        self,
        patch_body: PatchBody,
        id_col: <M::Entity as EntityTrait>::Column,
        update_col: <M::Entity as EntityTrait>::Column,
    ) -> Result<Self> {
        let (conn, select_to_update, mut with_query) = self.into_inner();
        let select = select_to_update.cloned();

        let to_update = select.all().await?;

        // Return early if there is nothing to update.
        if to_update.is_empty() {
            return Ok((conn, select_to_update, with_query).into());
        }

        let values = to_update
            .into_iter()
            .map(|model| {
                let id = if let Value::Uuid(Some(uuid)) = model.get(id_col) {
                    uuid
                } else {
                    return Err(QueryError("expected uuid id column".to_string()));
                };

                let update = match patch_body.clone() {
                    PatchBody::NestedIngestId { ingest_id } => {
                        Self::patch_for_ingest_id(ingest_id.into_inner().0)?
                    }
                    PatchBody::UnnestedAttributes(attributes)
                    | PatchBody::NestedAttributes { attributes } => {
                        Self::patch_for_attributes(attributes.into_inner().0, update_col, model)?
                    }
                };

                Ok((Value::Uuid(Some(id)), update))
            })
            .collect::<Result<Vec<_>>>()?;

        let cte_id = Alias::new("id");
        let cte_attributes = Alias::new(update_col.to_string());
        let cte_name = Alias::new("update_with");

        // select * from (values ((<id_to_update>, <attributes_to_update>), ...)
        let update_values = SelectStatement::new()
            .column(Asterisk)
            .from_values(values, Alias::new("values"))
            .to_owned();

        // with update_with(id, attributes) as (<update_values>)
        let cte = CommonTableExpression::new()
            .query(update_values)
            .columns([cte_id.clone(), cte_attributes.clone()])
            .table_name(cte_name.clone())
            .to_owned();
        let with_clause = WithClause::new().cte(cte).to_owned();

        // select attributes from update_with where object_id = id
        let select_update = SelectStatement::new()
            .column(cte_attributes)
            .from(cte_name.clone())
            .and_where(Expr::col(id_col).eq(Expr::col(cte_id.clone())))
            .to_owned();
        // select id in update_with
        let select_in = SelectStatement::new()
            .column(cte_id)
            .from(cte_name)
            .to_owned();

        // <with_clause>
        // update object set attributes = <select_update> where object_id in <select_in>
        // returning ...
        let returning =
            Query::returning().exprs(E::Column::iter().map(|c| c.select_as(Expr::col(c))));
        let update = E::update_many()
            .into_query()
            .value(
                update_col,
                SimpleExpr::SubQuery(None, Box::new(select_update.into_sub_query_statement())),
            )
            .and_where(id_col.in_subquery(select_in))
            .returning(returning)
            .to_owned();

        with_query = update.with(with_clause);

        let self_return: Self = (conn, select_to_update, with_query).into();

        self_return.trace_query("update_attributes");

        Ok(self_return)
    }

    fn trace_query(&self, message: &str) {
        self.select_to_update.trace_query(message);
    }
}

#[cfg(test)]
pub(crate) mod tests {
    use std::ops::{Index, Range};

    use sea_orm::{ActiveModelTrait, IntoActiveModel};
    use sea_orm::{DatabaseConnection, Set};
    use serde_json::json;
    use serde_json::{from_value, Value};
    use sqlx::PgPool;

    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::Client;
    use crate::queries::{Entries, EntriesBuilder};
    use crate::routes::filter::wildcard::Wildcard;
    use crate::routes::filter::wildcard::WildcardEither;

    use super::*;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_unsupported(pool: PgPool) {
        let client = Client::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(&client).await.unwrap();

        change_many(
            &client,
            &entries,
            &[0, 1],
            Some(json!({"attributeId": "1"})),
        )
        .await;

        let patch = json!([
            { "op": "remove", "path": "/attributeId" },
        ]);
        let results = test_s3_builder_result(
            &client,
            Some(json!({
                "attributeId": "1"
            })),
            PatchBody::new(from_value(patch).unwrap()),
        )
        .await;
        assert!(matches!(results, Err(InvalidQuery(_))));

        let patch = json!([
            { "op": "test", "path": "/attributeId", "value": "1" },
            { "op": "replace", "path": "/attributeId", "value": "attributeId" },
        ]);
        let results = test_s3_builder_result(
            &client,
            Some(json!({
                "attributeId": "1"
            })),
            PatchBody::new(from_value(patch).unwrap()),
        )
        .await;
        assert!(matches!(results, Err(InvalidQuery(_))));

        let patch = json!([
            { "op": "test", "path": "/attributeId", "value": "1" },
            { "op": "add", "path": "/attributeId", "value": "attributeId" },
        ]);
        let results = test_s3_builder_result(
            &client,
            Some(json!({
                "attributeId": "1"
            })),
            PatchBody::new(from_value(patch).unwrap()),
        )
        .await;
        assert!(matches!(results, Err(InvalidQuery(_))));

        entries_many(&mut entries, &[0, 1], json!({"attributeId": "1"}));
        assert_correct_records(&client, entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_add(pool: PgPool) {
        let client = Client::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(&client).await.unwrap();

        change_many(
            &client,
            &entries,
            &[0, 1],
            Some(json!({"attributeId": "1"})),
        )
        .await;

        let patch = json!([
            { "op": "add", "path": "/anotherAttribute", "value": "1" },
        ]);

        let results = test_update_with_attribute_id(&client, patch).await;

        entries_many(
            &mut entries,
            &[0, 1],
            json!({"attributeId": "1", "anotherAttribute": "1"}),
        );

        assert_contains(&results, &entries, 0..2);
        assert_correct_records(&client, entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_ingest_id(pool: PgPool) {
        let client = Client::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(&client).await.unwrap();

        change_many(
            &client,
            &entries,
            &[0, 1],
            Some(json!({"attributeId": "1"})),
        )
        .await;
        update_ingest_ids(&client, &mut entries).await;

        let patch = json!({
            "ingestId": [
                { "op": "add", "path": "/", "value": "00000000-0000-0000-0000-000000000000" },
            ]
        });

        let results = test_s3_builder_result(
            &client,
            Some(json!({
                "attributeId": "1"
            })),
            from_value(patch).unwrap(),
        )
        .await
        .unwrap()
        .all()
        .await
        .unwrap();

        entries_many(&mut entries, &[0, 1], json!({"attributeId": "1"}));
        entries.s3_objects[0].ingest_id = Some(Uuid::default());
        entries.s3_objects[1].ingest_id = Some(Uuid::default());

        assert_contains(&results, &entries, 0..2);
        assert_correct_records(&client, entries.clone()).await;

        let patch = json!({
            "ingestId": [
                { "op": "replace", "path": "/", "value": "00000000-0000-0000-0000-000000000001" },
            ]
        });

        let results = test_s3_builder_result(
            &client,
            Some(json!({
                "attributeId": "1"
            })),
            from_value(patch).unwrap(),
        )
        .await
        .unwrap()
        .all()
        .await
        .unwrap();

        entries_many(&mut entries, &[0, 1], json!({"attributeId": "1"}));
        entries.s3_objects[0].ingest_id =
            Some("00000000-0000-0000-0000-000000000001".parse().unwrap());
        entries.s3_objects[1].ingest_id =
            Some("00000000-0000-0000-0000-000000000001".parse().unwrap());

        assert_contains(&results, &entries, 0..2);
        assert_correct_records(&client, entries.clone()).await;

        let patch = json!({
            "ingestId": [
                { "op": "remove", "path": "/" },
            ]
        });

        let results = test_s3_builder_result(
            &client,
            Some(json!({
                "attributeId": "1"
            })),
            from_value(patch).unwrap(),
        )
        .await
        .unwrap()
        .all()
        .await
        .unwrap();

        entries_many(&mut entries, &[0, 1], json!({"attributeId": "1"}));
        entries.s3_objects[0].ingest_id = None;
        entries.s3_objects[1].ingest_id = None;

        assert_contains(&results, &entries, 0..2);
        assert_correct_records(&client, entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_ingest_id_error(pool: PgPool) {
        let client = Client::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(&client).await.unwrap();

        change_many(
            &client,
            &entries,
            &[0, 1],
            Some(json!({"attributeId": "1"})),
        )
        .await;

        update_ingest_ids(&client, &mut entries).await;

        let patch = json!({
            "ingestId": [
                { "op": "add", "path": "/", "value": "00000000-0000-0000-0000-00000000000" },
            ]
        });
        assert_ingest_id_error(&client, patch).await;

        let patch = json!({
            "ingestId": [
                { "op": "add", "path": "/ingestId", "value": "00000000-0000-0000-0000-000000000000" },
            ]
        });
        assert_ingest_id_error(&client, patch).await;

        let patch = json!({
            "ingestId": [
                { "op": "test", "path": "/", "value": "00000000-0000-0000-0000-00000000000" },
            ]
        });
        assert_ingest_id_error(&client, patch).await;

        let patch = json!({
            "ingestId": [
                { "op": "add", "path": "/", "value": "00000000-0000-0000-0000-00000000000" },
                { "op": "add", "path": "/", "value": "00000000-0000-0000-0000-00000000000" },
            ]
        });
        assert_ingest_id_error(&client, patch).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_add_wildcard(pool: PgPool) {
        let client = Client::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(&client).await.unwrap();

        change_many(
            &client,
            &entries,
            &[0, 1],
            Some(json!({"attributeId": "attributeId"})),
        )
        .await;

        let patch = json!([
            { "op": "add", "path": "/anotherAttribute", "value": "1" },
        ]);

        let results = test_update_attributes(
            &client,
            patch,
            Some(json!({
                "attributeId": "*a*"
            })),
        )
        .await;

        entries_many(
            &mut entries,
            &[0, 1],
            json!({"attributeId": "attributeId", "anotherAttribute": "1"}),
        );

        assert_contains(&results, &entries, 0..2);
        assert_correct_records(&client, entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_current_state(pool: PgPool) {
        let client = Client::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(&client).await.unwrap();

        change_many(
            &client,
            &entries,
            &[0, 1],
            Some(json!({"attributeId": "1"})),
        )
        .await;

        let patch = json!([
            { "op": "add", "path": "/anotherAttribute", "value": "1" },
        ]);

        let results = UpdateQueryBuilder::<_, s3_object::Entity>::new(client.connection_ref())
            .filter_all(
                S3ObjectsFilter {
                    attributes: Some(json!({
                    "attributeId": "1"
                    })),
                    ..Default::default()
                },
                true,
                true,
            )
            .unwrap()
            .update_s3_attributes(PatchBody::new(from_value(patch).unwrap()))
            .await
            .unwrap()
            .all()
            .await
            .unwrap();

        // Only the created event should be updated.
        entries.s3_objects[0].attributes =
            Some(json!({"attributeId": "1", "anotherAttribute": "1"}));
        entries.s3_objects[1].attributes = Some(json!({"attributeId": "1"}));

        assert_model_contains(&results, &entries.s3_objects, 0..1);
        assert_correct_records(&client, entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_wildcard_like(pool: PgPool) {
        let client = Client::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(&client).await.unwrap();

        change_many(
            &client,
            &entries,
            &[0, 2, 4, 6, 8],
            Some(json!({"attributeId": "1"})),
        )
        .await;

        let patch = json!([
            { "op": "add", "path": "/anotherAttribute", "value": "1" },
        ]);

        let results = UpdateQueryBuilder::<_, s3_object::Entity>::new(client.connection_ref())
            .filter_all(
                S3ObjectsFilter {
                    event_time: vec![WildcardEither::Wildcard(Wildcard::new(
                        "1970-01-0*".to_string(),
                    ))]
                    .into(),
                    ..Default::default()
                },
                true,
                true,
            )
            .unwrap()
            .update_s3_attributes(PatchBody::new(from_value(patch).unwrap()))
            .await
            .unwrap()
            .all()
            .await
            .unwrap();

        assert_wildcard_update(&mut entries, &results);
        assert_correct_records(&client, entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_add_from_null_json(pool: PgPool) {
        let client = Client::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(&client).await.unwrap();

        change_many(&client, &entries, &[0, 1], Some(Value::Null)).await;

        let patch = json!([
            { "op": "add", "path": "/anotherAttribute", "value": "1" },
        ]);

        let results = test_update_attributes(&client, patch, Some(Value::Null)).await;

        entries_many(&mut entries, &[0, 1], json!({"anotherAttribute": "1"}));

        assert_contains(&results, &entries, 0..2);
        assert_correct_records(&client, entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_add_from_not_set(pool: PgPool) {
        let client = Client::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(&client).await.unwrap();

        null_attributes(&client, &entries, 0).await;

        let patch = json!([
            { "op": "add", "path": "/anotherAttribute", "value": "1" },
        ]);

        let results =
            test_update_attributes_for_id(&client, patch, entries.s3_objects[0].s3_object_id).await;

        change_attribute_entries(&mut entries, 0, json!({"anotherAttribute": "1"}));

        assert_contains(&results, &entries, 0..1);
        assert_correct_records(&client, entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_no_op(pool: PgPool) {
        let client = Client::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(&client).await.unwrap();

        change_many(
            &client,
            &entries,
            &[0, 1],
            Some(json!({"attributeId": "2"})),
        )
        .await;

        let patch = json!([
            { "op": "add", "path": "/anotherAttribute", "value": "3" },
        ]);

        let results = test_update_with_attribute_id(&client, patch).await;

        entries_many(&mut entries, &[0, 1], json!({"attributeId": "2"}));

        assert!(results.is_empty());
        assert_correct_records(&client, entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_failed_test(pool: PgPool) {
        let client = Client::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(&client).await.unwrap();

        change_many(
            &client,
            &entries,
            &[0, 1],
            Some(json!({"attributeId": "1"})),
        )
        .await;

        let patch = json!([
            { "op": "add", "path": "/anotherAttribute", "value": "anotherAttribute" },
            { "op": "test", "path": "/attributeId", "value": "2" },
        ]);

        let s3_objects = test_s3_builder_result(
            &client,
            Some(json!({
                "attributeId": "1"
            })),
            PatchBody::new(from_value(patch).unwrap()),
        )
        .await;

        assert!(matches!(s3_objects, Err(InvalidQuery(_))));

        // Nothing should be updated here.
        entries_many(&mut entries, &[0, 1], json!({"attributeId": "1"}));
        assert_correct_records(&client, entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_replace_different_attribute_ids(pool: PgPool) {
        let client = Client::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(&client).await.unwrap();

        change_attributes(&client, &entries, 0, Some(json!({"attributeId": "2"}))).await;
        change_attributes(&client, &entries, 1, Some(json!({"attributeId": "2"}))).await;
        change_attributes(&client, &entries, 2, Some(json!({"attributeId": "2"}))).await;

        let patch = json!([
            { "op": "add", "path": "/anotherAttribute", "value": "anotherAttribute" },
        ]);

        let results_s3_objects = test_update_attributes(
            &client,
            patch.clone(),
            Some(json!({
                "attributeId": "2"
            })),
        )
        .await;

        entries_many(
            &mut entries,
            &[0, 1, 2],
            json!({"attributeId": "2", "anotherAttribute": "anotherAttribute"}),
        );

        assert_model_contains(&results_s3_objects, &entries.s3_objects, 0..3);
        assert_correct_records(&client, entries).await;
    }

    async fn assert_ingest_id_error(client: &Client, patch: Value) {
        assert!(test_s3_builder_result(
            client,
            Some(json!({
                "attributeId": "1"
            })),
            from_value(patch).unwrap()
        )
        .await
        .is_err());
    }

    async fn test_s3_builder_result(
        client: &Client,
        attributes: Option<Value>,
        patch_body: PatchBody,
    ) -> Result<UpdateQueryBuilder<DatabaseConnection, s3_object::Entity>> {
        UpdateQueryBuilder::<_, s3_object::Entity>::new(client.connection_ref())
            .filter_all(
                S3ObjectsFilter {
                    attributes,
                    ..Default::default()
                },
                true,
                false,
            )?
            .update_s3_attributes(patch_body)
            .await
    }

    async fn test_update_attributes(
        client: &Client,
        patch: Value,
        attributes: Option<Value>,
    ) -> Vec<s3_object::Model> {
        test_s3_builder_result(
            client,
            attributes,
            PatchBody::new(from_value(patch).unwrap()),
        )
        .await
        .unwrap()
        .all()
        .await
        .unwrap()
    }

    async fn test_update_attributes_for_id(
        client: &Client,
        patch: Value,
        s3_object_id: Uuid,
    ) -> Vec<s3_object::Model> {
        UpdateQueryBuilder::<_, s3_object::Entity>::new(client.connection_ref())
            .for_id(s3_object_id)
            .update_s3_attributes(PatchBody::new(from_value(patch).unwrap()))
            .await
            .unwrap()
            .all()
            .await
            .unwrap()
    }

    async fn test_update_with_attribute_id(client: &Client, patch: Value) -> Vec<s3_object::Model> {
        test_update_attributes(
            client,
            patch,
            Some(json!({
                "attributeId": "1"
            })),
        )
        .await
    }

    pub(crate) fn assert_wildcard_update(entries: &mut Entries, results: &[s3_object::Model]) {
        for i in [0, 2, 4, 6, 8] {
            // Only the created event should be updated.
            entries.s3_objects[i].attributes =
                Some(json!({"attributeId": "1", "anotherAttribute": "1"}));

            assert_model_contains(&[results[i / 2].clone()], &entries.s3_objects, i..i + 1);
        }
    }

    pub(crate) async fn update_ingest_ids(client: &Client, entries: &mut Entries) {
        for i in [0, 1] {
            let mut model: s3_object::ActiveModel =
                entries.s3_objects[i].clone().into_active_model();
            model.ingest_id = Set(None);
            model.update(client.connection_ref()).await.unwrap();
        }
    }

    /// Make attributes null for an entry.
    pub(crate) async fn null_attributes(client: &Client, entries: &Entries, entry: usize) {
        change_attributes(client, entries, entry, None).await;
    }

    /// Change multiple attributes in the database.
    pub(crate) async fn change_many(
        client: &Client,
        entries: &Entries,
        indices: &[usize],
        value: Option<Value>,
    ) {
        for i in indices {
            change_attributes(client, entries, *i, value.clone()).await;
        }
    }

    pub(crate) async fn change_attributes(
        client: &Client,
        entries: &Entries,
        entry: usize,
        value: Option<Value>,
    ) {
        let mut model: s3_object::ActiveModel =
            entries.s3_objects[entry].clone().into_active_model();
        model.attributes = Set(value);
        model.update(client.connection_ref()).await.unwrap();
    }

    pub(crate) async fn change_key(
        client: &Client,
        entries: &Entries,
        entry: usize,
        value: String,
    ) {
        let mut model: s3_object::ActiveModel =
            entries.s3_objects[entry].clone().into_active_model();
        model.key = Set(value);
        model.update(client.connection_ref()).await.unwrap();
    }

    /// Change attributes in the entries.
    pub(crate) fn change_attribute_entries(entries: &mut Entries, entry: usize, value: Value) {
        entries.s3_objects[entry].attributes = Some(value.clone());
    }

    /// Change multiple attributes in the entries.
    pub(crate) fn entries_many(entries: &mut Entries, indices: &[usize], value: Value) {
        for i in indices {
            change_attribute_entries(entries, *i, value.clone());
        }
    }

    pub(crate) fn assert_model_contains<M>(objects: &[M], contains: &[M], range: Range<usize>)
    where
        M: Eq + PartialEq,
    {
        let contains_objects = contains.index(range.clone());
        assert_eq!(objects.len(), contains_objects.len());

        contains_objects
            .iter()
            .for_each(|value| assert!(objects.contains(value)));
    }

    /// Assert that the result contains the values.
    pub(crate) fn assert_contains(
        s3_objects: &[s3_object::Model],
        contains: &Entries,
        range: Range<usize>,
    ) {
        assert_model_contains(s3_objects, &contains.s3_objects, range.clone());
    }

    /// Assert that no existing records are updated.
    pub(crate) async fn assert_correct_records(client: &Client, entries: Entries) {
        let s3_objects = ListQueryBuilder::<_, s3_object::Entity>::new(client.connection_ref())
            .all()
            .await
            .unwrap();

        assert_eq!(s3_objects, entries.s3_objects);
    }
}
