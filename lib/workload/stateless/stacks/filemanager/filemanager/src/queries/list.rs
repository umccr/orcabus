//! Query builder involving list operations on the database.
//!

use sea_orm::{EntityTrait, FromQueryResult, PaginatorTrait, QuerySelect, Select};

use crate::database::entities::object::Entity as ObjectEntity;
use crate::database::entities::s3_object::Entity as S3ObjectEntity;
use crate::database::Client;
use crate::error::Error::OverflowError;
use crate::error::{Error, Result};
use crate::routes::list::{ListCount, ListResponse, Pagination};

/// A query builder for list operations.
pub struct ListQueryBuilder<'a, T>
where
    T: EntityTrait,
{
    client: &'a Client,
    select: Select<T>,
}

impl<'a> ListQueryBuilder<'a, ObjectEntity> {
    /// Create a new query builder.
    pub fn new(client: &'a Client) -> Self {
        Self {
            client,
            select: Self::build_object(),
        }
    }

    /// Build a select query for finding values from objects.
    pub fn build_object() -> Select<ObjectEntity> {
        ObjectEntity::find()
    }
}

impl<'a> ListQueryBuilder<'a, S3ObjectEntity> {
    /// Create a new query builder.
    pub fn new(client: &'a Client) -> Self {
        Self {
            client,
            select: Self::build_object(),
        }
    }

    /// Build a select query for finding values from s3 objects.
    pub fn build_object() -> Select<S3ObjectEntity> {
        S3ObjectEntity::find()
    }
}

impl<'a, T, M> ListQueryBuilder<'a, T>
where
    T: EntityTrait<Model = M>,
    M: FromQueryResult + Send + Sync,
{
    /// Execute the prepared query, fetching all values.
    pub async fn all(self) -> Result<Vec<M>> {
        Ok(self.select.all(self.client.connection_ref()).await?)
    }

    /// Execute the prepared query, fetching one value.
    pub async fn one(self) -> Result<Option<M>> {
        Ok(self.select.one(self.client.connection_ref()).await?)
    }

    /// Execute the prepared query, counting all values.
    pub async fn count(self) -> Result<u64> {
        Ok(self.select.count(self.client.connection_ref()).await?)
    }

    /// Paginate the query for the given page and page_size.
    pub async fn paginate(mut self, page: u64, page_size: u64) -> Result<Self> {
        let offset = page.checked_mul(page_size).ok_or_else(|| OverflowError)?;
        // Always add one to the limit to see if there is additional pages that can be fetched.
        let limit = page_size.checked_add(1).ok_or_else(|| OverflowError)?;

        self.select = self.select.offset(offset).limit(limit);
        Ok(self)
    }

    /// Create a list response from pagination query parameters and a query builder.
    pub async fn paginate_to_list_response(
        self,
        pagination: Pagination,
    ) -> Result<ListResponse<M>> {
        let query = self.paginate(pagination.page, pagination.page_size).await?;

        let mut results = query.all().await?;

        // Check if there are more pages using the knowledge that we fetched one additional record.
        let next_page = if results.len()
            <= usize::try_from(pagination.page_size)
                .map_err(|err| Error::ConversionError(err.to_string()))?
        {
            None
        } else {
            // Remove the last element because we fetched one additional result.
            results.pop();
            Some(pagination.page_size)
        };

        Ok(ListResponse::new(results, next_page))
    }

    /// Create a list count from a query builder.
    pub async fn to_list_count(self) -> Result<ListCount> {
        Ok(ListCount::new(self.count().await?))
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
    async fn test_list_objects(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = initialize_database(&client, 10).await;

        let builder = ListQueryBuilder::<ObjectEntity>::new(&client);
        let result = builder.all().await.unwrap();

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

        let builder = ListQueryBuilder::<S3ObjectEntity>::new(&client);
        let result = builder.all().await.unwrap();

        assert_eq!(
            result,
            entries
                .into_iter()
                .map(|(_, entry)| entry)
                .collect::<Vec<_>>()
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_count_objects(pool: PgPool) {
        let client = Client::from_pool(pool);
        initialize_database(&client, 10).await;

        let builder = ListQueryBuilder::<ObjectEntity>::new(&client);
        let result = builder.count().await.unwrap();

        assert_eq!(result, 10);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_count_s3_objects(pool: PgPool) {
        let client = Client::from_pool(pool);
        initialize_database(&client, 10).await;

        let builder = ListQueryBuilder::<S3ObjectEntity>::new(&client);
        let result = builder.count().await.unwrap();

        assert_eq!(result, 10);
    }
}
