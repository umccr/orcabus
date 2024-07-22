//! Query builder to handle updating record columns.
//!

use crate::database::entities::object::Column as ObjectColumn;
use crate::database::entities::s3_object::Column as S3ObjectColumn;
use crate::error::Result;
use sea_orm::prelude::Expr;
use sea_orm::sea_query::extension::postgres::PgExpr;
use sea_orm::sea_query::{Func, FunctionCall, PostgresQueryBuilder};
use sea_orm::{
    ColumnTrait, ConnectionTrait, EntityTrait, QueryFilter, QueryTrait, UpdateMany,
};
use serde_json::json;
use tracing::trace;
use uuid::Uuid;

use crate::database::entities::object::{ActiveModel as ObjectActiveModel, Entity as ObjectEntity};
use crate::database::entities::s3_object::Entity as S3ObjectEntity;
use crate::routes::attributes::AttributeBody;

/// A query builder for list operations.
#[derive(Debug, Clone)]
pub struct UpdateQueryBuilder<'a, C, E>
where
    E: EntityTrait,
{
    connection: &'a C,
    update: UpdateMany<E>,
}

impl<'a, C> UpdateQueryBuilder<'a, C, ObjectEntity>
where
    C: ConnectionTrait,
{
    /// Create a new query builder.
    pub fn new(connection: &'a C) -> Self {
        Self {
            connection,
            update: Self::for_objects(),
        }
    }

    /// Define an update query for finding values from objects.
    pub fn for_objects() -> UpdateMany<ObjectEntity> {
        ObjectEntity::update_many()
    }

    /// Update the attributes on an object replacing any existing keys in the attributes.
    pub fn for_id(mut self, id: Uuid) -> Self {
        self.update = self.update.filter(ObjectColumn::ObjectId.eq(id));

        self
    }

    /// Update the attributes on an object replacing any existing keys in the attributes.
    pub fn update_attributes_replace(mut self, attributes: AttributeBody) -> Self {
        // Right-hand side replaces left-hand side, so the new attributes goes to
        // the right for replacement.
        self.update = self.update.col_expr(
            ObjectColumn::Attributes,
            Expr::expr(Self::coalesce_attributes()).concat(attributes.into_object()),
        );

        self.trace_query("update_attributes_replace");

        self
    }

    /// Update the attributes on an object replacing any existing keys in the attributes.
    pub fn update_attributes_insert(mut self, attributes: AttributeBody) -> Self {
        // Right-hand side replaces left-hand side, so the old attributes goes to
        // the right for insert.
        self.update = self.update.col_expr(
            ObjectColumn::Attributes,
            Expr::expr(attributes.into_object()).concat(Self::coalesce_attributes()),
        );

        self.trace_query("update_attributes_insert");

        self
    }

    /// Whenever updating attributes, this function should be called to coalesce
    /// a possible null attribute value so that the update with new attributes
    /// succeeds.
    fn coalesce_attributes() -> FunctionCall {
        Func::coalesce([
            Expr::col(ObjectColumn::Attributes).into(),
            Expr::val(json!({})).into(),
        ])
    }
}

impl<'a, C, E, M> UpdateQueryBuilder<'a, C, E>
where
    C: ConnectionTrait,
    E: EntityTrait<Model = M>,
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

    fn trace_query(&self, message: &str) {
        trace!(
            "{message}: {}",
            self.update.as_query().to_string(PostgresQueryBuilder)
        );
    }
}

#[cfg(test)]
mod tests {
    use serde_json::Value;
    use serde_json::{json, Map};
    use sqlx::PgPool;

    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::entities::object::Model;
    use crate::database::Client;
    use crate::queries::tests::initialize_database;

    use super::*;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_update_attributes_replace_none(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = initialize_database(&client, 10).await.objects;

        null_attributes(&client, &entries).await;

        let input = vec![("another_id".to_string(), json!("attribute_id"))];
        let result = test_update_replace(&client, &entries, input).await;

        let mut expected = entries[0].clone();
        expected.attributes = Some(json!({"another_id": "attribute_id"}));

        // A new value should be inserted.
        assert_eq!(result.unwrap(), expected);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_update_attributes_replace(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = initialize_database(&client, 10).await.objects;

        let input = vec![(
            "attribute_id".to_string(),
            json!({ "nested_id": "attribute_id" }),
        )];
        let result = test_update_replace(&client, &entries, input).await;

        let mut expected = entries[0].clone();
        expected.attributes.as_mut().unwrap()["attribute_id"] =
            json!({"nested_id": "attribute_id"});

        // A conflicting key should replace.
        assert_eq!(result.unwrap(), expected);

        let input = vec![("another_id".to_string(), json!("0"))];
        let result = test_update_replace(&client, &entries, input).await;

        expected.attributes.as_mut().unwrap()["another_id"] = json!("0");

        // A non-conflicting key should also insert.
        assert_eq!(result.unwrap(), expected);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_update_attributes_insert_none(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = initialize_database(&client, 10).await.objects;

        null_attributes(&client, &entries).await;

        let input = vec![("another_id".to_string(), json!("attribute_id"))];
        let result = test_update_insert(&client, &entries, input).await;

        let mut expected = entries[0].clone();
        expected.attributes = Some(json!({"another_id": "attribute_id"}));

        // A new value should be inserted.
        assert_eq!(result.unwrap(), expected);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_update_attributes_insert(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = initialize_database(&client, 10).await.objects;

        let input = vec![(
            "attribute_id".to_string(),
            json!({ "nested_id": "attribute_id" }),
        )];
        let result = test_update_insert(&client, &entries, input).await;

        // No Update expected as this key already exists.
        let expected = entries[0].clone();
        assert_eq!(result.unwrap(), expected);

        let input = vec![("another_id".to_string(), json!("0"))];
        let result = test_update_insert(&client, &entries, input).await;

        // Inserting without a conflict should proceed as normal.
        let mut expected = entries[0].clone();
        expected.attributes.as_mut().unwrap()["another_id"] = json!("0");

        assert_eq!(result.unwrap(), expected);
    }

    async fn test_update_replace(
        client: &Client,
        entries: &[Model],
        input: Vec<(String, Value)>,
    ) -> Option<Model> {
        UpdateQueryBuilder::new(client.connection_ref())
            .for_id(entries[0].object_id)
            .update_attributes_replace(AttributeBody::new(Map::from_iter(input)))
            .one()
            .await
            .unwrap()
    }

    async fn test_update_insert(
        client: &Client,
        entries: &[Model],
        input: Vec<(String, Value)>,
    ) -> Option<Model> {
        UpdateQueryBuilder::new(client.connection_ref())
            .for_id(entries[0].object_id)
            .update_attributes_insert(AttributeBody::new(Map::from_iter(input)))
            .one()
            .await
            .unwrap()
    }

    async fn null_attributes(client: &Client, entries: &[Model]) {
        UpdateQueryBuilder::new(client.connection_ref())
            .for_id(entries[0].object_id)
            .update
            .col_expr(ObjectColumn::Attributes, Expr::cust("null"))
            .exec(client.connection_ref())
            .await
            .unwrap();
    }
}
