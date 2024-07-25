//! Query builder to handle updating record columns.
//!

use json_patch::patch;
use sea_orm::prelude::{Expr, Json};
use sea_orm::sea_query::{
    Alias, Asterisk, CommonTableExpression, PostgresQueryBuilder, Query, SelectStatement,
    SimpleExpr, WithClause, WithQuery,
};
use sea_orm::{
    ColumnTrait, ConnectionTrait, EntityTrait, FromQueryResult, Iterable, ModelTrait, QueryFilter,
    QueryTrait, Select, StatementBuilder, Value,
};
use serde_json::json;
use tracing::trace;
use uuid::Uuid;

use crate::database::entities::{object, s3_object};
use crate::error::Error::{InvalidQuery, QueryError};
use crate::error::Result;
use crate::queries::list::ListQueryBuilder;
use crate::routes::filtering::{ObjectsFilterAll, S3ObjectsFilterAll};
use crate::routes::update::PatchBody;

/// A query builder for list operations.
#[derive(Debug, Clone)]
pub struct UpdateQueryBuilder<'a, C, E>
where
    E: EntityTrait,
{
    connection: &'a C,
    select_to_update: Select<E>,
    // With query will eventually end up as the update
    update: WithQuery,
}

impl<'a, C> UpdateQueryBuilder<'a, C, object::Entity>
where
    C: ConnectionTrait,
{
    /// Create a new query builder.
    pub fn new(connection: &'a C) -> Self {
        Self {
            connection,
            select_to_update: object::Entity::find(),
            update: WithQuery::new(),
        }
    }

    /// Update the attributes on an object replacing any existing keys in the attributes.
    pub fn for_id(mut self, id: Uuid) -> Self {
        self.select_to_update = self
            .select_to_update
            .filter(object::Column::ObjectId.eq(id));

        self
    }

    /// Filter records by all fields in the filter variable.
    pub fn filter_all(mut self, filter: ObjectsFilterAll) -> Self {
        self.select_to_update = self
            .select_to_update
            .filter(ListQueryBuilder::<object::Entity>::filter_condition(filter));

        self.trace_query("filter_all");

        self
    }

    /// Update the attributes on an object using the attribute patch.
    pub async fn update_object_attributes(self, patch: PatchBody) -> Result<Self> {
        self.update_attributes(patch, object::Column::ObjectId, object::Column::Attributes)
            .await
    }
}

impl<'a, C> UpdateQueryBuilder<'a, C, s3_object::Entity>
where
    C: ConnectionTrait,
{
    /// Create a new query builder.
    pub fn new(connection: &'a C) -> Self {
        Self {
            connection,
            select_to_update: s3_object::Entity::find(),
            update: WithQuery::new(),
        }
    }

    /// Update the attributes on an object replacing any existing keys in the attributes.
    pub fn for_id(mut self, id: Uuid) -> Self {
        self.select_to_update = self
            .select_to_update
            .filter(s3_object::Column::S3ObjectId.eq(id));

        self
    }

    /// Filter records by all fields in the filter variable.
    pub fn filter_all(mut self, filter: S3ObjectsFilterAll) -> Self {
        self.select_to_update =
            self.select_to_update
                .filter(ListQueryBuilder::<s3_object::Entity>::filter_condition(
                    filter,
                ));

        self.trace_query("filter_all");

        self
    }

    /// Update the attributes on an s3_object using the attribute patch.
    pub async fn update_s3_object_attributes(self, patch: PatchBody) -> Result<Self> {
        self.update_attributes(
            patch,
            s3_object::Column::S3ObjectId,
            s3_object::Column::Attributes,
        )
        .await
    }
}

impl<'a, C, E, M> UpdateQueryBuilder<'a, C, E>
where
    C: ConnectionTrait,
    E: EntityTrait<Model = M>,
    M: ModelTrait + FromQueryResult,
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
    /// update <object|s3_object> set attributes = (
    ///     select attributes from update_with where object_id = id
    /// ) where object_id in (select id from update_with)
    /// returning <updated_objects>
    /// ```
    pub async fn update_attributes(
        mut self,
        patch_body: PatchBody,
        id_col: <M::Entity as EntityTrait>::Column,
        attribute_col: <M::Entity as EntityTrait>::Column,
    ) -> Result<Self> {
        let to_update = self.select_to_update.clone().all(self.connection).await?;

        // Return early if there is nothing to update.
        if to_update.is_empty() {
            return Ok(self);
        }

        let values = to_update
            .into_iter()
            .map(|model| {
                let id = if let Value::Uuid(Some(uuid)) = model.get(id_col) {
                    uuid
                } else {
                    return Err(QueryError("expected uuid id column".to_string()));
                };

                let mut current = if let Value::Json(json) = model.get(attribute_col) {
                    let mut json = json.unwrap_or_else(|| Box::new(json!({})));
                    if let &Json::Null = json.as_ref() {
                        json = Box::new(json!({}));
                    }
                    json
                } else {
                    return Err(QueryError("expected JSON attribute column".to_string()));
                };

                // Patch it based on JSON patch.
                patch(&mut current, &patch_body.get_ref().0).map_err(|err| {
                    InvalidQuery(format!(
                        "JSON patch {} operation for {} path failed: {}",
                        err.operation, err.path, err.kind
                    ))
                })?;

                Ok((Value::Uuid(Some(id)), Value::Json(Some(current))))
            })
            .collect::<Result<Vec<_>>>()?;

        let cte_id = Alias::new("id");
        let cte_attributes = Alias::new("attributes");
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
                attribute_col,
                SimpleExpr::SubQuery(None, Box::new(select_update.into_sub_query_statement())),
            )
            .and_where(id_col.in_subquery(select_in))
            .returning(returning)
            .to_owned();

        self.update = update.with(with_clause);

        self.trace_query("update_attributes");

        Ok(self)
    }

    fn trace_query(&self, message: &str) {
        trace!(
            "{message}: {}",
            self.select_to_update
                .as_query()
                .to_string(PostgresQueryBuilder)
        );
        trace!("{message}: {}", self.update.to_string(PostgresQueryBuilder));
    }
}

#[cfg(test)]
pub(crate) mod tests {

    use std::ops::{Index, Range};

    use crate::queries::{Entries, EntriesBuilder};
    use sea_orm::{ActiveModelTrait, IntoActiveModel};
    use sea_orm::{DatabaseConnection, Set};
    use serde_json::json;
    use serde_json::{from_value, Value};
    use sqlx::PgPool;

    use crate::database::aws::migration::tests::MIGRATOR;

    use crate::database::Client;

    use super::*;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_replace(pool: PgPool) {
        let client = Client::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(&client).await;

        change_attributes(&client, &entries, 0, Some(json!({"attribute_id": "1"}))).await;
        change_attributes(&client, &entries, 1, Some(json!({"attribute_id": "1"}))).await;

        let patch = json!([
            { "op": "test", "path": "/attribute_id", "value": "1" },
            { "op": "replace", "path": "/attribute_id", "value": "attribute_id" },
        ]);

        let results = test_update_with_attribute_id(&client, patch).await;

        change_attribute_entries(&mut entries, 0, json!({"attribute_id": "attribute_id"})).await;
        change_attribute_entries(&mut entries, 1, json!({"attribute_id": "attribute_id"})).await;

        assert_contains(&results.0, &results.1, &entries, 0..2);
        assert_correct_records(&client, entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_add(pool: PgPool) {
        let client = Client::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(&client).await;

        change_attributes(&client, &entries, 0, Some(json!({"attribute_id": "1"}))).await;
        change_attributes(&client, &entries, 1, Some(json!({"attribute_id": "1"}))).await;

        let patch = json!([
            { "op": "add", "path": "/another_attribute", "value": "1" },
        ]);

        let results = test_update_with_attribute_id(&client, patch).await;

        change_attribute_entries(
            &mut entries,
            0,
            json!({"attribute_id": "1", "another_attribute": "1"}),
        )
        .await;
        change_attribute_entries(
            &mut entries,
            1,
            json!({"attribute_id": "1", "another_attribute": "1"}),
        )
        .await;

        assert_contains(&results.0, &results.1, &entries, 0..2);
        assert_correct_records(&client, entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_add_from_null_json(pool: PgPool) {
        let client = Client::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(&client).await;

        change_attributes(&client, &entries, 0, Some(Value::Null)).await;
        change_attributes(&client, &entries, 1, Some(Value::Null)).await;

        let patch = json!([
            { "op": "add", "path": "/another_attribute", "value": "1" },
        ]);

        let results = test_update_attributes(&client, patch, Some(Value::Null)).await;

        change_attribute_entries(&mut entries, 0, json!({"another_attribute": "1"})).await;
        change_attribute_entries(&mut entries, 1, json!({"another_attribute": "1"})).await;

        assert_contains(&results.0, &results.1, &entries, 0..2);
        assert_correct_records(&client, entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_add_from_not_set(pool: PgPool) {
        let client = Client::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(&client).await;

        null_attributes(&client, &entries, 0).await;

        let patch = json!([
            { "op": "add", "path": "/another_attribute", "value": "1" },
        ]);

        let results = test_update_attributes_for_id(
            &client,
            patch,
            entries.objects[0].object_id,
            entries.s3_objects[0].s3_object_id,
        )
        .await;

        change_attribute_entries(&mut entries, 0, json!({"another_attribute": "1"})).await;

        assert_contains(&results.0, &results.1, &entries, 0..1);
        assert_correct_records(&client, entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_remove(pool: PgPool) {
        let client = Client::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(&client).await;

        change_attributes(&client, &entries, 0, Some(json!({"attribute_id": "1"}))).await;
        change_attributes(&client, &entries, 1, Some(json!({"attribute_id": "1"}))).await;

        let patch = json!([
            { "op": "remove", "path": "/attribute_id" },
        ]);

        let results = test_update_with_attribute_id(&client, patch).await;

        change_attribute_entries(&mut entries, 0, json!({})).await;
        change_attribute_entries(&mut entries, 1, json!({})).await;

        assert_contains(&results.0, &results.1, &entries, 0..2);
        assert_correct_records(&client, entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_no_op(pool: PgPool) {
        let client = Client::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(&client).await;

        change_attributes(&client, &entries, 0, Some(json!({"attribute_id": "2"}))).await;
        change_attributes(&client, &entries, 1, Some(json!({"attribute_id": "2"}))).await;

        let patch = json!([
            { "op": "remove", "path": "/attribute_id" },
        ]);

        let results = test_update_with_attribute_id(&client, patch).await;

        change_attribute_entries(&mut entries, 0, json!({"attribute_id": "2"})).await;
        change_attribute_entries(&mut entries, 1, json!({"attribute_id": "2"})).await;

        assert!(results.0.is_empty());
        assert!(results.1.is_empty());
        assert_correct_records(&client, entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_failed_test(pool: PgPool) {
        let client = Client::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(&client).await;

        change_attributes(&client, &entries, 0, Some(json!({"attribute_id": "1"}))).await;
        change_attributes(&client, &entries, 1, Some(json!({"attribute_id": "1"}))).await;

        let patch = json!([
            { "op": "replace", "path": "/attribute_id", "value": "attribute_id" },
            { "op": "test", "path": "/attribute_id", "value": "2" },
        ]);

        let objects = test_object_builder_result(
            &client,
            patch.clone(),
            Some(json!({
                "attribute_id": "1"
            })),
        )
        .await;
        let s3_objects = test_s3_object_builder_result(
            &client,
            patch,
            Some(json!({
                "attribute_id": "1"
            })),
        )
        .await;

        assert!(matches!(objects, Err(InvalidQuery(_))));
        assert!(matches!(s3_objects, Err(InvalidQuery(_))));

        // Nothing should be updated here.
        change_attribute_entries(&mut entries, 0, json!({"attribute_id": "1"})).await;
        change_attribute_entries(&mut entries, 1, json!({"attribute_id": "1"})).await;
        assert_correct_records(&client, entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_for_id(pool: PgPool) {
        let client = Client::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(&client).await;

        change_attributes(&client, &entries, 0, Some(json!({"attribute_id": "1"}))).await;

        let patch = json!([
            { "op": "test", "path": "/attribute_id", "value": "1" },
            { "op": "replace", "path": "/attribute_id", "value": "attribute_id" },
        ]);

        let result = test_update_attributes_for_id(
            &client,
            patch,
            entries.objects[0].object_id,
            entries.s3_objects[0].s3_object_id,
        )
        .await;

        change_attribute_entries(&mut entries, 0, json!({"attribute_id": "attribute_id"})).await;

        assert_contains(&result.0, &result.1, &entries, 0..1);
        assert_correct_records(&client, entries).await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn update_attributes_replace_different_attribute_ids(pool: PgPool) {
        let client = Client::from_pool(pool);
        let mut entries = EntriesBuilder::default().build(&client).await;

        change_object_attributes(&client, &entries, 0, Some(json!({"attribute_id": "1"}))).await;
        change_object_attributes(&client, &entries, 1, Some(json!({"attribute_id": "1"}))).await;
        change_object_attributes(&client, &entries, 2, Some(json!({"attribute_id": "1"}))).await;

        change_s3_object_attributes(&client, &entries, 0, Some(json!({"attribute_id": "2"}))).await;
        change_s3_object_attributes(&client, &entries, 1, Some(json!({"attribute_id": "2"}))).await;
        change_s3_object_attributes(&client, &entries, 2, Some(json!({"attribute_id": "2"}))).await;

        let patch = json!([
            { "op": "replace", "path": "/attribute_id", "value": "attribute_id" },
        ]);

        let results_objects = test_update_attributes(
            &client,
            patch.clone(),
            Some(json!({
                "attribute_id": "1"
            })),
        )
        .await;
        let results_s3_objects = test_update_attributes(
            &client,
            patch.clone(),
            Some(json!({
                "attribute_id": "2"
            })),
        )
        .await;

        change_attribute_entries(&mut entries, 0, json!({"attribute_id": "attribute_id"})).await;
        change_attribute_entries(&mut entries, 1, json!({"attribute_id": "attribute_id"})).await;
        change_attribute_entries(&mut entries, 2, json!({"attribute_id": "attribute_id"})).await;

        assert_model_contains(&results_objects.0, &entries.objects, 0..3);
        assert_model_contains(&results_s3_objects.1, &entries.s3_objects, 0..3);
        assert_correct_records(&client, entries).await;
    }

    async fn test_object_builder_result(
        client: &Client,
        patch: Value,
        attributes: Option<Value>,
    ) -> Result<UpdateQueryBuilder<DatabaseConnection, object::Entity>> {
        UpdateQueryBuilder::<_, object::Entity>::new(client.connection_ref())
            .filter_all(ObjectsFilterAll { attributes })
            .update_object_attributes(PatchBody::new(from_value(patch).unwrap()))
            .await
    }

    async fn test_s3_object_builder_result(
        client: &Client,
        patch: Value,
        attributes: Option<Value>,
    ) -> Result<UpdateQueryBuilder<DatabaseConnection, s3_object::Entity>> {
        UpdateQueryBuilder::<_, s3_object::Entity>::new(client.connection_ref())
            .filter_all(S3ObjectsFilterAll {
                attributes,
                ..Default::default()
            })
            .update_s3_object_attributes(PatchBody::new(from_value(patch).unwrap()))
            .await
    }

    async fn test_update_attributes(
        client: &Client,
        patch: Value,
        attributes: Option<Value>,
    ) -> (Vec<object::Model>, Vec<s3_object::Model>) {
        (
            test_object_builder_result(client, patch.clone(), attributes.clone())
                .await
                .unwrap()
                .all()
                .await
                .unwrap(),
            test_s3_object_builder_result(client, patch, attributes)
                .await
                .unwrap()
                .all()
                .await
                .unwrap(),
        )
    }

    async fn test_update_attributes_for_id(
        client: &Client,
        patch: Value,
        object_id: Uuid,
        s3_object_id: Uuid,
    ) -> (Vec<object::Model>, Vec<s3_object::Model>) {
        (
            UpdateQueryBuilder::<_, object::Entity>::new(client.connection_ref())
                .for_id(object_id)
                .update_object_attributes(PatchBody::new(from_value(patch.clone()).unwrap()))
                .await
                .unwrap()
                .all()
                .await
                .unwrap(),
            UpdateQueryBuilder::<_, s3_object::Entity>::new(client.connection_ref())
                .for_id(s3_object_id)
                .update_s3_object_attributes(PatchBody::new(from_value(patch).unwrap()))
                .await
                .unwrap()
                .all()
                .await
                .unwrap(),
        )
    }

    async fn test_update_with_attribute_id(
        client: &Client,
        patch: Value,
    ) -> (Vec<object::Model>, Vec<s3_object::Model>) {
        test_update_attributes(
            client,
            patch,
            Some(json!({
                "attribute_id": "1"
            })),
        )
        .await
    }

    /// Make attributes null for an entry.
    pub(crate) async fn null_attributes(client: &Client, entries: &Entries, entry: usize) {
        change_attributes(client, entries, entry, None).await;
    }

    /// Change attributes in the database.
    pub(crate) async fn change_attributes(
        client: &Client,
        entries: &Entries,
        entry: usize,
        value: Option<Value>,
    ) {
        change_object_attributes(client, entries, entry, value.clone()).await;
        change_s3_object_attributes(client, entries, entry, value).await;
    }

    async fn change_s3_object_attributes(
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

    async fn change_object_attributes(
        client: &Client,
        entries: &Entries,
        entry: usize,
        value: Option<Value>,
    ) {
        let mut model: object::ActiveModel = entries.objects[entry].clone().into_active_model();
        model.attributes = Set(value);
        model.update(client.connection_ref()).await.unwrap();
    }

    /// Change attributes in the database.
    pub(crate) async fn change_attribute_entries(
        entries: &mut Entries,
        entry: usize,
        value: Value,
    ) {
        entries.s3_objects[entry].attributes = Some(value.clone());
        entries.objects[entry].attributes = Some(value);
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
        objects: &[object::Model],
        s3_objects: &[s3_object::Model],
        contains: &Entries,
        range: Range<usize>,
    ) {
        assert_model_contains(objects, &contains.objects, range.clone());
        assert_model_contains(s3_objects, &contains.s3_objects, range.clone());
    }

    /// Assert that no existing records are updated.
    pub(crate) async fn assert_correct_records(client: &Client, mut entries: Entries) {
        let mut objects = ListQueryBuilder::<object::Entity>::new(client)
            .all()
            .await
            .unwrap();
        let s3_objects = ListQueryBuilder::<s3_object::Entity>::new(client)
            .all()
            .await
            .unwrap();

        objects.sort_by_key(|value| value.object_id);
        entries.objects.sort_by_key(|value| value.object_id);

        assert_eq!(objects, entries.objects);
        assert_eq!(s3_objects, entries.s3_objects);
    }
}
