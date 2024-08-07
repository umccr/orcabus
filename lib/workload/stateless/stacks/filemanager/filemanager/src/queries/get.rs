//! Query builder involving get operations on the database.
//!

use sea_orm::{EntityTrait, Select};
use uuid::Uuid;

use crate::database::entities::{object, s3_object};
use crate::database::Client;
use crate::error::Result;

/// A query builder for get operations.
pub struct GetQueryBuilder<'a> {
    client: &'a Client,
}

impl<'a> GetQueryBuilder<'a> {
    /// Create a new query builder.
    pub fn new(client: &'a Client) -> Self {
        Self { client }
    }

    /// Build a select query for finding an object by id.
    pub fn build_object_by_id(id: Uuid) -> Select<object::Entity> {
        object::Entity::find_by_id(id)
    }

    /// Build a select query for finding an s3 object by id.
    pub fn build_s3_object_by_id(id: Uuid) -> Select<s3_object::Entity> {
        s3_object::Entity::find_by_id(id)
    }

    /// Get a specific object by id.
    pub async fn get_object(&self, id: Uuid) -> Result<Option<object::Model>> {
        Ok(Self::build_object_by_id(id)
            .one(self.client.connection_ref())
            .await?)
    }

    /// Get a specific s3 object by id.
    pub async fn get_s3_object_by_id(&self, id: Uuid) -> Result<Option<s3_object::Model>> {
        Ok(Self::build_s3_object_by_id(id)
            .one(self.client.connection_ref())
            .await?)
    }
}

#[cfg(test)]
mod tests {
    use sqlx::PgPool;

    use super::*;
    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::Client;
    use crate::queries::EntriesBuilder;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_get_object(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = EntriesBuilder::default().build(&client).await.objects;

        let first = entries.first().unwrap();
        let builder = GetQueryBuilder::new(&client);
        let result = builder.get_object(first.object_id).await.unwrap();

        assert_eq!(result.as_ref(), Some(first));
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_list_s3_objects(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = EntriesBuilder::default().build(&client).await.s3_objects;

        let first = entries.first().unwrap();
        let builder = GetQueryBuilder::new(&client);
        let result = builder
            .get_s3_object_by_id(first.s3_object_id)
            .await
            .unwrap();

        assert_eq!(result.as_ref(), Some(first));
    }
}
