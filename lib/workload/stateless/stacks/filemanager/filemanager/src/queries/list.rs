//! Query builder involving list operations on the database.
//!

use sea_orm::{EntityTrait, PaginatorTrait, Select};

use crate::database::entities::object_group::Entity as ObjectGroupEntity;
use crate::database::entities::object_group::Model as ObjectGroup;
use crate::database::entities::s3_object::Entity as S3ObjectEntity;
use crate::database::entities::s3_object::Model as S3Object;
use crate::database::Client;
use crate::error::Result;

/// A query builder for list operations.
pub struct ListQueryBuilder<'a> {
    client: &'a Client,
}

impl<'a> ListQueryBuilder<'a> {
    /// Create a new query builder.
    pub fn new(client: &'a Client) -> Self {
        Self { client }
    }

    /// Build a select query for finding values from object groups.
    pub fn build_object_group() -> Select<ObjectGroupEntity> {
        ObjectGroupEntity::find()
    }

    /// Build a select query for finding values from s3 objects.
    pub fn build_s3_object() -> Select<S3ObjectEntity> {
        S3ObjectEntity::find()
    }

    /// Find all object groups.
    pub async fn list_object_groups(&self) -> Result<Vec<ObjectGroup>> {
        Ok(Self::build_object_group()
            .all(self.client.connection_ref())
            .await?)
    }

    /// Find all s3 objects.
    pub async fn list_s3_objects(&self) -> Result<Vec<S3Object>> {
        Ok(Self::build_s3_object()
            .all(self.client.connection_ref())
            .await?)
    }

    /// Count object groups.
    pub async fn count_object_groups(&self) -> Result<u64> {
        Ok(Self::build_object_group()
            .count(self.client.connection_ref())
            .await?)
    }

    /// Count s3 objects.
    pub async fn count_s3_objects(&self) -> Result<u64> {
        Ok(Self::build_s3_object()
            .count(self.client.connection_ref())
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
    async fn test_list_object_groups(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = initialize_database(&client, 10).await;

        let builder = ListQueryBuilder::new(&client);
        let result = builder.list_object_groups().await.unwrap();

        assert_eq!(
            result,
            entries
                .into_iter()
                .map(|(entry, _)| entry)
                .collect::<Vec<_>>()
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_list_s3_objects(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = initialize_database(&client, 10).await;

        let builder = ListQueryBuilder::new(&client);
        let result = builder.list_s3_objects().await.unwrap();

        assert_eq!(
            result,
            entries
                .into_iter()
                .map(|(_, entry)| entry)
                .collect::<Vec<_>>()
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_count_object_groups(pool: PgPool) {
        let client = Client::from_pool(pool);
        initialize_database(&client, 10).await;

        let builder = ListQueryBuilder::new(&client);
        let result = builder.count_object_groups().await.unwrap();

        assert_eq!(result, 10);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_count_s3_objects(pool: PgPool) {
        let client = Client::from_pool(pool);
        initialize_database(&client, 10).await;

        let builder = ListQueryBuilder::new(&client);
        let result = builder.count_s3_objects().await.unwrap();

        assert_eq!(result, 10);
    }
}
