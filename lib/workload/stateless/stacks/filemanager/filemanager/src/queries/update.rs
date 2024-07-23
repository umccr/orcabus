//! Query builder to handle updating record columns.
//!

use sea_orm::prelude::Expr;
use sea_orm::sea_query::extension::postgres::PgExpr;
use sea_orm::sea_query::{Func, FunctionCall, PostgresQueryBuilder};
use sea_orm::{
    ColumnTrait, ConnectionTrait, EntityTrait, ModelTrait, QueryFilter, QueryTrait, UpdateMany,
};
use serde_json::json;
use tracing::trace;
use uuid::Uuid;

use crate::database::entities::object;
use crate::error::Error::{InvalidQuery, QueryError};
use crate::error::Result;
use crate::queries::list::ListQueryBuilder;
use crate::routes::attributes::{AttributeBody, MergeStrategy};
use crate::routes::filtering::ObjectsFilterAll;

/// A query builder for list operations.
#[derive(Debug, Clone)]
pub struct UpdateQueryBuilder<'a, C, E>
where
    E: EntityTrait,
{
    connection: &'a C,
    update: UpdateMany<E>,
}

impl<'a, C> UpdateQueryBuilder<'a, C, object::Entity>
where
    C: ConnectionTrait,
{
    /// Create a new query builder.
    pub fn new(connection: &'a C) -> Self {
        Self {
            connection,
            update: Self::build_for_objects(),
        }
    }

    /// Define an update query for finding values from objects.
    pub fn build_for_objects() -> UpdateMany<object::Entity> {
        object::Entity::update_many()
    }

    /// Update the attributes on an object replacing any existing keys in the attributes.
    pub fn for_id(mut self, id: Uuid) -> Self {
        self.update = self.update.filter(object::Column::ObjectId.eq(id));

        self
    }

    /// Filter records by all fields in the filter variable.
    pub fn filter_all(mut self, filter: ObjectsFilterAll) -> Self {
        self.update = self
            .update
            .filter(ListQueryBuilder::filter_condition(filter));
        self
    }

    /// Execute the prepared query according to the merge strategy.
    pub async fn for_objects(
        self,
        attributes: AttributeBody,
        merge_strategy: MergeStrategy,
    ) -> Result<Vec<object::Model>> {
        self.for_merge_strategy(attributes, merge_strategy, object::Column::Attributes)
            .await
    }
}

impl<'a, C, E, M> UpdateQueryBuilder<'a, C, E>
where
    C: ConnectionTrait,
    E: EntityTrait<Model = M>,
    M: ModelTrait,
{
    /// Execute the prepared query, returning all values.
    pub async fn all(self) -> Result<Vec<M>> {
        Ok(self.update.exec_with_returning(self.connection).await?)
    }

    /// Execute the prepared query, returning one value.
    pub async fn one(self) -> Result<Option<M>> {
        Ok(self
            .update
            .exec_with_returning(self.connection)
            .await?
            .into_iter()
            .nth(0))
    }

    /// Update the attributes on an object replacing any existing keys in the attributes.
    /// This function should receive the attribute column to operate on, e.g. `Object::Attributes`.
    pub fn update_attributes_replace(
        mut self,
        attributes: AttributeBody,
        c: <M::Entity as EntityTrait>::Column,
    ) -> Self {
        // Right-hand side replaces left-hand side, so the new attributes goes to
        // the right for replacement.
        self.update = self.update.col_expr(
            c,
            Expr::expr(Self::coalesce_attributes(c)).concat(attributes.into_object()),
        );

        self.trace_query("update_attributes_replace");

        self
    }

    /// Update the attributes on an object replacing any existing keys in the attributes.
    /// This function should receive the attribute column to operate on, e.g. `Object::Attributes`.
    pub fn update_attributes_insert(
        mut self,
        attributes: AttributeBody,
        c: <M::Entity as EntityTrait>::Column,
    ) -> Self {
        // Right-hand side replaces left-hand side, so the old attributes goes to
        // the right for insert.
        self.update = self.update.col_expr(
            c,
            Expr::expr(attributes.into_object()).concat(Self::coalesce_attributes(c)),
        );

        self.trace_query("update_attributes_insert");

        self
    }

    /// Whenever updating attributes, this function should be called to coalesce
    /// a possible null attribute value so that the update with new attributes
    /// succeeds. This function should receive the attribute column to operate on,
    /// e.g. `Object::Attributes`.
    fn coalesce_attributes(c: <M::Entity as EntityTrait>::Column) -> FunctionCall {
        Func::coalesce([Expr::col(c).into(), Expr::val(json!({})).into()])
    }

    /// Execute the prepared query as an insert, returning an error if
    /// any attribute keys already exist. This function should receive the
    /// attribute column to operate on, e.g. `Object::Attributes`.
    pub async fn for_insert(
        self,
        attributes: AttributeBody,
        c: <M::Entity as EntityTrait>::Column,
    ) -> Result<Vec<M>> {
        let inserted = self
            .update_attributes_insert(attributes.clone(), c)
            .all()
            .await?;

        for model in &inserted {
            let column = model.get(c);
            let merged = column
                .as_ref_json()
                .ok_or_else(|| QueryError("expected JSON attributes column".to_string()))?;
            let default = Default::default();
            let merged = merged.as_object().unwrap_or(&default);

            let conflict = attributes
                .get_ref()
                .into_iter()
                .map(|(key, value)| {
                    // If the new merged value does not equal the requested update attributes
                    // then this means that the same key was present in the existing attributes.
                    merged
                        .get(key)
                        .map(|merged_value| merged_value != value)
                        .unwrap_or_default()
                })
                .find(|value| *value)
                .unwrap_or_default();

            if conflict {
                return Err(InvalidQuery(
                    "a key already exists using insert merge strategy".to_string(),
                ));
            }
        }

        Ok(inserted)
    }

    /// Execute the prepared query as an insert, where non-existent keys are merged
    /// and any existing keys are ignored. This function should receive the
    /// attribute column to operate on, e.g. `Object::Attributes`.
    pub async fn for_insert_non_existent(
        self,
        attributes: AttributeBody,
        c: <M::Entity as EntityTrait>::Column,
    ) -> Result<Vec<M>> {
        self.update_attributes_insert(attributes.clone(), c)
            .all()
            .await
    }

    /// Execute the prepared query as a replace, where all keys are merged and
    /// existing keys are replaced. This function should receive the
    /// attribute column to operate on, e.g. `Object::Attributes`.
    pub async fn for_replace(
        self,
        attributes: AttributeBody,
        c: <M::Entity as EntityTrait>::Column,
    ) -> Result<Vec<M>> {
        self.update_attributes_replace(attributes.clone(), c)
            .all()
            .await
    }

    /// Execute the prepared query according to the merge strategy. This
    /// function should receive the attribute column to operate on,
    /// e.g. `Object::Attributes`.
    pub async fn for_merge_strategy(
        self,
        attributes: AttributeBody,
        merge_strategy: MergeStrategy,
        c: <M::Entity as EntityTrait>::Column,
    ) -> Result<Vec<M>> {
        match merge_strategy {
            MergeStrategy::Insert => self.for_insert(attributes, c).await,
            MergeStrategy::InsertNonExistent => self.for_insert_non_existent(attributes, c).await,
            MergeStrategy::Replace => self.for_replace(attributes, c).await,
        }
    }

    fn trace_query(&self, message: &str) {
        trace!(
            "{message}: {}",
            self.update.as_query().to_string(PostgresQueryBuilder)
        );
    }
}

#[cfg(test)]
pub(crate) mod tests {
    use super::*;
    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::entities::object::Model;
    use crate::database::Client;
    use crate::queries::tests::initialize_database;
    use crate::queries::update::tests::TestStrategy::{
        Insert, InsertNonExist, InsertNonExistNotNull, InsertNotNull, Replace, ReplaceNotNull,
    };
    use serde_json::Value;
    use serde_json::{json, Map};
    use sqlx::PgPool;
    use std::future::Future;

    /// Create parameterized tests for updating attributes.
    #[derive(Debug)]
    enum TestStrategy {
        Replace,
        ReplaceNotNull,
        InsertNonExist,
        InsertNonExistNotNull,
        Insert,
        InsertNotNull,
    }

    impl TestStrategy {
        async fn assert<F, Fut>(&self, pool: PgPool, model_func: F)
        where
            F: Fn(Client, Vec<Model>, Vec<(String, Value)>) -> Fut,
            Fut: Future<Output = Result<Vec<Model>>>,
        {
            let client = Client::from_pool(pool);
            let entries = initialize_database(&client, 10).await.objects;

            let input = vec![(
                "attribute_id".to_string(),
                json!({ "nested_id": "attribute_id" }),
            )];

            let result = model_func(client.clone(), entries.clone(), input).await;

            let mut expected = entries[0].clone();
            match self {
                Replace | ReplaceNotNull => {
                    expected.attributes.as_mut().unwrap()["attribute_id"] =
                        json!({"nested_id": "attribute_id"});
                }
                _ => {}
            }

            match self {
                Insert | InsertNotNull => assert!(result.is_err()),
                _ => assert_eq!(result.unwrap()[0], expected),
            }

            match self {
                Replace | InsertNonExist | Insert => {
                    null_attributes(&client, &entries[0]).await;
                    expected = entries[0].clone();
                    expected.attributes = Some(json!({"another_id": "0"}));
                }
                ReplaceNotNull | InsertNonExistNotNull | InsertNotNull => {
                    expected.attributes.as_mut().unwrap()["another_id"] = json!("0");
                }
            }

            let input = vec![("another_id".to_string(), json!("0"))];
            let result = model_func(client.clone(), entries.clone(), input).await;

            // A non-conflicting key should also insert.
            assert_eq!(result.unwrap()[0], expected);

            assert_correct_records(&client, entries, &[expected.object_id]).await;
            clear_tables(&client).await;
        }
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_update_attributes_replace(pool: PgPool) {
        ReplaceNotNull
            .assert(pool.clone(), |client, entries, input| async move {
                test_update_replace(&client, &entries, input).await
            })
            .await;
        ReplaceNotNull
            .assert(pool.clone(), |client, entries, input| async move {
                test_merge_strategy_replace(&client, &entries, input).await
            })
            .await;
        Replace
            .assert(pool.clone(), |client, entries, input| async move {
                test_update_replace(&client, &entries, input).await
            })
            .await;
        Replace
            .assert(pool, |client, entries, input| async move {
                test_merge_strategy_replace(&client, &entries, input).await
            })
            .await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_update_attributes_insert(pool: PgPool) {
        InsertNonExistNotNull
            .assert(pool.clone(), |client, entries, input| async move {
                test_update_insert(&client, &entries, input).await
            })
            .await;
        InsertNonExistNotNull
            .assert(pool.clone(), |client, entries, input| async move {
                test_merge_strategy_insert_non_existent(&client, &entries, input).await
            })
            .await;
        InsertNonExist
            .assert(pool.clone(), |client, entries, input| async move {
                test_update_insert(&client, &entries, input).await
            })
            .await;
        InsertNonExist
            .assert(pool.clone(), |client, entries, input| async move {
                test_merge_strategy_insert_non_existent(&client, &entries, input).await
            })
            .await;
        InsertNotNull
            .assert(pool.clone(), |client, entries, input| async move {
                test_merge_strategy_insert(&client, &entries, input).await
            })
            .await;
        Insert
            .assert(pool, |client, entries, input| async move {
                test_merge_strategy_insert(&client, &entries, input).await
            })
            .await;
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_update_attributes_filter(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = initialize_database(&client, 10).await.objects;

        let input = vec![(
            "attribute_id".to_string(),
            json!({ "nested_id": "attribute_id" }),
        )];
        let result = filter_all_objects_replace(
            &client,
            ObjectsFilterAll {
                attributes: Some(json!({
                    "attribute_id": "1"
                })),
            },
            input.clone(),
        )
        .await;

        let mut expected = entries[1].clone();
        expected.attributes.as_mut().unwrap()["attribute_id"] =
            json!({"nested_id": "attribute_id"});

        assert_eq!(result, vec![expected]);

        let result = filter_all_objects_replace(
            &client,
            ObjectsFilterAll {
                attributes: Some(json!({
                    "non_existent_id": "1"
                })),
            },
            input,
        )
        .await;
        assert!(result.is_empty());
    }

    async fn clear_tables(client: &Client) {
        client
            .connection_ref()
            .execute_unprepared("truncate table s3_object, object")
            .await
            .unwrap();
    }

    async fn filter_all_objects_replace(
        client: &Client,
        filter: ObjectsFilterAll,
        input: Vec<(String, Value)>,
    ) -> Vec<Model> {
        UpdateQueryBuilder::new(client.connection_ref())
            .filter_all(filter)
            .update_attributes_replace(
                AttributeBody::new(Map::from_iter(input)),
                object::Column::Attributes,
            )
            .all()
            .await
            .unwrap()
    }

    async fn test_update_replace(
        client: &Client,
        entries: &[Model],
        input: Vec<(String, Value)>,
    ) -> Result<Vec<Model>> {
        Ok(vec![UpdateQueryBuilder::new(client.connection_ref())
            .for_id(entries[0].object_id)
            .update_attributes_replace(
                AttributeBody::new(Map::from_iter(input)),
                object::Column::Attributes,
            )
            .one()
            .await
            .unwrap()
            .unwrap()])
    }

    async fn test_merge_strategy_replace(
        client: &Client,
        entries: &[Model],
        input: Vec<(String, Value)>,
    ) -> Result<Vec<Model>> {
        UpdateQueryBuilder::new(client.connection_ref())
            .for_id(entries[0].object_id)
            .for_objects(
                AttributeBody::new(Map::from_iter(input)),
                MergeStrategy::Replace,
            )
            .await
    }

    async fn test_merge_strategy_insert(
        client: &Client,
        entries: &[Model],
        input: Vec<(String, Value)>,
    ) -> Result<Vec<Model>> {
        UpdateQueryBuilder::new(client.connection_ref())
            .for_id(entries[0].object_id)
            .for_objects(
                AttributeBody::new(Map::from_iter(input)),
                MergeStrategy::Insert,
            )
            .await
    }

    async fn test_merge_strategy_insert_non_existent(
        client: &Client,
        entries: &[Model],
        input: Vec<(String, Value)>,
    ) -> Result<Vec<Model>> {
        UpdateQueryBuilder::new(client.connection_ref())
            .for_id(entries[0].object_id)
            .for_objects(
                AttributeBody::new(Map::from_iter(input)),
                MergeStrategy::InsertNonExistent,
            )
            .await
    }

    async fn test_update_insert(
        client: &Client,
        entries: &[Model],
        input: Vec<(String, Value)>,
    ) -> Result<Vec<Model>> {
        Ok(vec![UpdateQueryBuilder::new(client.connection_ref())
            .for_id(entries[0].object_id)
            .update_attributes_insert(
                AttributeBody::new(Map::from_iter(input)),
                object::Column::Attributes,
            )
            .one()
            .await
            .unwrap()
            .unwrap()])
    }

    /// Make attributes null for an entry.
    pub(crate) async fn null_attributes(client: &Client, entry: &Model) {
        change_attributes(client, entry, "null").await;
    }

    /// Make attributes null for an entry.
    pub(crate) async fn change_attributes(client: &Client, entry: &Model, value: &str) {
        UpdateQueryBuilder::new(client.connection_ref())
            .for_id(entry.object_id)
            .update
            .col_expr(object::Column::Attributes, Expr::cust(value))
            .exec(client.connection_ref())
            .await
            .unwrap();
    }

    /// Assert that no existing records are updated.
    pub(crate) async fn assert_correct_records(
        client: &Client,
        entries: Vec<Model>,
        affected: &[Uuid],
    ) {
        let mut objects = ListQueryBuilder::<object::Entity>::new(client)
            .all()
            .await
            .unwrap();
        objects.retain(|object| !affected.contains(&object.object_id));
        assert_eq!(objects, entries[affected.len()..]);
    }
}
