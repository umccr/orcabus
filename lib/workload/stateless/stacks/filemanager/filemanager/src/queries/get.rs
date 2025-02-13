//! Query builder involving get operations on the database.
//!

use sea_orm::{ConnectionTrait, EntityTrait, Select};
use uuid::Uuid;

use crate::database::entities::{s3_crawl, s3_object};
use crate::error::Result;

/// A query builder for get operations.
pub struct GetQueryBuilder<'a, C> {
    connection: &'a C,
}

impl<'a, C> GetQueryBuilder<'a, C>
where
    C: ConnectionTrait,
{
    /// Create a new query builder.
    pub fn new(connection: &'a C) -> Self {
        Self { connection }
    }

    /// Build a select query for finding an s3 object by id.
    pub fn build_s3_by_id(id: Uuid) -> Select<s3_object::Entity> {
        s3_object::Entity::find_by_id(id)
    }

    /// Get a specific s3 object by id.
    pub async fn get_s3_by_id(&self, id: Uuid) -> Result<Option<s3_object::Model>> {
        Ok(Self::build_s3_by_id(id).one(self.connection).await?)
    }

    /// Build a select query for finding an crawl row by id.
    pub fn build_crawl_by_id(id: Uuid) -> Select<s3_crawl::Entity> {
        s3_crawl::Entity::find_by_id(id)
    }

    /// Get a specific crawl row by id.
    pub async fn get_crawl_by_id(&self, id: Uuid) -> Result<Option<s3_crawl::Model>> {
        Ok(Self::build_crawl_by_id(id).one(self.connection).await?)
    }
}

#[cfg(test)]
mod tests {
    use sqlx::PgPool;

    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::Client;
    use crate::queries::EntriesBuilder;

    use super::*;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_get_s3(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = EntriesBuilder::default()
            .build(&client)
            .await
            .unwrap()
            .s3_objects;

        let first = entries.first().unwrap();
        let builder = GetQueryBuilder::new(client.connection_ref());
        let result = builder.get_s3_by_id(first.s3_object_id).await.unwrap();

        assert_eq!(result.as_ref(), Some(first));
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_get_crawl(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = EntriesBuilder::default()
            .build(&client)
            .await
            .unwrap()
            .s3_crawl;

        let first = entries.first().unwrap();
        let builder = GetQueryBuilder::new(client.connection_ref());
        let result = builder.get_crawl_by_id(first.s3_crawl_id).await.unwrap();

        assert_eq!(result.as_ref(), Some(first));
    }
}
