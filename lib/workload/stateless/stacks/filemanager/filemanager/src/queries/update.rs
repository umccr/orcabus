//! Query builder to handle updating record columns.
//!

use crate::database::entities::object::Column as ObjectColumn;
use crate::database::entities::s3_object::Column as S3ObjectColumn;
use crate::database::Client;
use crate::error::Result;
use sea_orm::prelude::Expr;
use sea_orm::sea_query::extension::postgres::PgExpr;
use sea_orm::sea_query::PostgresQueryBuilder;
use sea_orm::{ColumnTrait, EntityTrait, QueryFilter, QueryTrait, UpdateMany};
use tracing::trace;
use uuid::Uuid;

use crate::database::entities::object::{ActiveModel as ObjectActiveModel, Entity as ObjectEntity};
use crate::database::entities::s3_object::Entity as S3ObjectEntity;
use crate::routes::attributes::AttributeBody;

/// A query builder for list operations.
#[derive(Debug, Clone)]
pub struct UpdateQueryBuilder<'a, E>
where
    E: EntityTrait,
{
    client: &'a Client,
    update: UpdateMany<E>,
}

impl<'a> UpdateQueryBuilder<'a, ObjectEntity> {
    /// Create a new query builder.
    pub fn new(client: &'a Client) -> Self {
        Self {
            client,
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

        self.trace_query("for_id");

        self
    }

    /// Update the attributes on an object replacing any existing keys in the attributes.
    pub fn update_attributes_replace(mut self, attributes: AttributeBody) -> Self {
        self.update = self.update.col_expr(
            ObjectColumn::Attributes,
            Expr::col(ObjectColumn::Attributes).concat(attributes.into_inner()),
        );

        self.trace_query("update_attributes_replace");

        self
    }
}

impl<'a, E, M> UpdateQueryBuilder<'a, E>
where
    E: EntityTrait<Model = M>,
{
    /// Execute the prepared query, returning all values.
    pub async fn all(self) -> Result<Vec<M>> {
        Ok(self
            .update
            .exec_with_returning(self.client.connection_ref())
            .await?)
    }

    /// Execute the prepared query, returning one value.
    pub async fn one(self) -> Result<Option<M>> {
        Ok(self
            .update
            .exec_with_returning(self.client.connection_ref())
            .await?
            .into_iter()
            .nth(0))
    }

    fn trace_query(&self, message: &str) {
        println!("{}", self.update.as_query().to_string(PostgresQueryBuilder));
        trace!(
            "{message}: {}",
            self.update.as_query().to_string(PostgresQueryBuilder)
        );
    }
}

#[cfg(test)]
mod tests {
    use serde_json::{json, Map};
    use sqlx::PgPool;

    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::queries::tests::initialize_database;

    use super::*;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_update_attributes_replace(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = initialize_database(&client, 10).await.objects;

        let builder = UpdateQueryBuilder::<ObjectEntity>::new(&client)
            .for_id(entries[0].object_id)
            .update_attributes_replace(AttributeBody::new(Map::from_iter(vec![(
                "attribute_id".to_string(),
                json!({ "nested_id": "attribute_id" }),
            )])));
        let result = builder.one().await.unwrap();

        let mut expected = entries[0].clone();
        expected.attributes = Some(
            json!({"nested_id": {"attribute_id": "0"}, "attribute_id": {"nested_id": "attribute_id"}}),
        );

        assert_eq!(result.unwrap(), expected);
    }
}
