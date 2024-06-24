//! Query builder involving get operations on the database.
//!

use sea_orm::{EntityTrait, Select};
use uuid::Uuid;

use crate::database::entities::object_group::Entity as ObjectGroupEntity;
use crate::database::entities::object_group::Model as ObjectGroup;
use crate::database::entities::s3_object::Entity as S3ObjectEntity;
use crate::database::entities::s3_object::Model as S3Object;
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

    /// Build a select query for finding an object group by id.
    pub fn build_object_group_by_id(id: Uuid) -> Select<ObjectGroupEntity> {
        ObjectGroupEntity::find_by_id(id)
    }

    /// Build a select query for finding an s3 object by id.
    pub fn build_s3_object_by_id(id: Uuid) -> Select<S3ObjectEntity> {
        S3ObjectEntity::find_by_id(id)
    }

    /// Get a specific object group by id.
    pub async fn get_object_group(&self, id: Uuid) -> Result<Option<ObjectGroup>> {
        Ok(Self::build_object_group_by_id(id)
            .one(self.client.connection_ref())
            .await?)
    }

    /// Get a specific s3 object by id.
    pub async fn get_s3_object_by_id(&self, id: Uuid) -> Result<Option<S3Object>> {
        Ok(Self::build_s3_object_by_id(id)
            .one(self.client.connection_ref())
            .await?)
    }
}

#[cfg(test)]
mod tests {
    use sqlx::PgPool;

    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::Client;
    use crate::queries::tests::initialize_database;

    use super::*;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_get_object_group(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = initialize_database(&client, 10).await;

        let first = entries.first().unwrap();
        let builder = GetQueryBuilder::new(&client);
        let result = builder.get_object_group(first.0.object_id).await.unwrap();

        assert_eq!(result.as_ref(), Some(&first.0));
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_list_s3_objects(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = initialize_database(&client, 10).await;

        let first = entries.first().unwrap();
        let builder = GetQueryBuilder::new(&client);
        let result = builder
            .get_s3_object_by_id(first.1.s3_object_id)
            .await
            .unwrap();

        assert_eq!(result.as_ref(), Some(&first.1));
    }
}
