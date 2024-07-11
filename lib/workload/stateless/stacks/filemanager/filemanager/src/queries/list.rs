//! Query builder involving list operations on the database.
//!

use sea_orm::prelude::Expr;
use sea_orm::sea_query::extension::postgres::PgExpr;
use sea_orm::{
    ColumnTrait, Condition, EntityTrait, FromQueryResult, PaginatorTrait, QueryFilter, QueryOrder,
    QuerySelect, Select,
};

use crate::database::entities::object::Entity as ObjectEntity;
use crate::database::entities::s3_object::Entity as S3ObjectEntity;
use crate::database::entities::s3_object::{Column as S3ObjectColumn, Column as ObjectColumn};
use crate::database::Client;
use crate::error::Error::OverflowError;
use crate::error::{Error, Result};
use crate::routes::filtering::{ObjectsFilterByAll, S3ObjectsFilterByAll};
use crate::routes::list::{ListCount, ListResponse};
use crate::routes::pagination::Pagination;

/// A query builder for list operations.
#[derive(Debug, Clone)]
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
            select: Self::build_objects(),
        }
    }

    /// Build a select query for finding values from objects.
    pub fn build_objects() -> Select<ObjectEntity> {
        ObjectEntity::find()
    }

    /// Filter records by all fields in the filter variable.
    pub async fn filter_all(mut self, filter: ObjectsFilterByAll) -> Self {
        let condition = Condition::all().add_option(
            filter
                .attributes
                .map(|v| Expr::col(ObjectColumn::Attributes).contains(v)),
        );

        self.select = self.select.filter(condition);
        self
    }
}

impl<'a> ListQueryBuilder<'a, S3ObjectEntity> {
    /// Create a new query builder.
    pub fn new(client: &'a Client) -> Self {
        Self {
            client,
            select: Self::build_s3_objects(),
        }
    }

    /// Build a select query for finding values from s3 objects.
    pub fn build_s3_objects() -> Select<S3ObjectEntity> {
        S3ObjectEntity::find().order_by_asc(S3ObjectColumn::Sequencer)
    }

    /// Filter records by all fields in the filter variable.
    pub async fn filter_all(mut self, filter: S3ObjectsFilterByAll) -> Self {
        let condition = Condition::all()
            .add_option(filter.event_type.map(|v| S3ObjectColumn::EventType.eq(v)))
            .add_option(filter.bucket.map(|v| S3ObjectColumn::Bucket.eq(v)))
            .add_option(filter.key.map(|v| S3ObjectColumn::Key.eq(v)))
            .add_option(filter.version_id.map(|v| S3ObjectColumn::VersionId.eq(v)))
            .add_option(filter.date.map(|v| S3ObjectColumn::Date.eq(v)))
            .add_option(filter.size.map(|v| S3ObjectColumn::Size.eq(v)))
            .add_option(filter.sha256.map(|v| S3ObjectColumn::Sha256.eq(v)))
            .add_option(
                filter
                    .last_modified_date
                    .map(|v| S3ObjectColumn::LastModifiedDate.eq(v)),
            )
            .add_option(filter.e_tag.map(|v| S3ObjectColumn::ETag.eq(v)))
            .add_option(
                filter
                    .storage_class
                    .map(|v| S3ObjectColumn::StorageClass.eq(v)),
            )
            .add_option(
                filter
                    .is_delete_marker
                    .map(|v| S3ObjectColumn::IsDeleteMarker.eq(v)),
            )
            .add_option(
                filter
                    .attributes
                    .map(|v| Expr::col(S3ObjectColumn::Attributes).contains(v)),
            );

        self.select = self.select.filter(condition);
        self
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
        let page = pagination.page();
        let page_size = pagination.page_size();
        let query = self.paginate(page, page_size).await?;

        let mut results = query.all().await?;

        // Check if there are more pages using the knowledge that we fetched one additional record.
        let next_page = if results.len()
            <= usize::try_from(page_size).map_err(|err| Error::ConversionError(err.to_string()))?
        {
            None
        } else {
            // Remove the last element because we fetched one additional result.
            results.pop();
            Some(page.checked_add(1).ok_or_else(|| OverflowError)?)
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
    use crate::queries::tests::{initialize_database, initialize_database_reorder};

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
    async fn test_paginate_objects(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = initialize_database(&client, 10).await;

        let builder = ListQueryBuilder::<ObjectEntity>::new(&client);

        let result = paginate_all(builder.clone(), 3, 3).await;
        assert_eq!(
            result,
            &entries
                .clone()
                .into_iter()
                .map(|(entry, _)| entry)
                .collect::<Vec<_>>()[9..]
        );
        // Empty result when paginating above the collection size.
        assert!(paginate_all(builder.clone(), 10, 2).await.is_empty());

        let result = builder
            .paginate_to_list_response(Pagination::new(0, 2))
            .await
            .unwrap();

        assert_eq!(result.next_page(), Some(1));
        assert_eq!(
            result.results(),
            &entries
                .into_iter()
                .map(|(entry, _)| entry)
                .collect::<Vec<_>>()[0..2]
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_list_s3_objects(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = initialize_database_reorder(&client, 10).await;

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
    async fn test_paginate_s3_objects(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = initialize_database_reorder(&client, 10).await;

        let builder = ListQueryBuilder::<S3ObjectEntity>::new(&client);

        let result = paginate_all(builder.clone(), 3, 3).await;
        assert_eq!(
            result,
            &entries
                .clone()
                .into_iter()
                .map(|(_, entry)| entry)
                .collect::<Vec<_>>()[9..]
        );
        // Empty result when paginating above the collection size.
        assert!(paginate_all(builder.clone(), 10, 2).await.is_empty());

        let result = builder
            .paginate_to_list_response(Pagination::new(0, 2))
            .await
            .unwrap();

        assert_eq!(result.next_page(), Some(1));
        assert_eq!(
            result.results(),
            &entries
                .into_iter()
                .map(|(_, entry)| entry)
                .collect::<Vec<_>>()[0..2]
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_count_objects(pool: PgPool) {
        let client = Client::from_pool(pool);
        initialize_database(&client, 10).await;

        let builder = ListQueryBuilder::<ObjectEntity>::new(&client);

        assert_eq!(builder.clone().count().await.unwrap(), 10);
        assert_eq!(builder.to_list_count().await.unwrap(), ListCount::new(10));
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_count_s3_objects(pool: PgPool) {
        let client = Client::from_pool(pool);
        initialize_database(&client, 10).await;

        let builder = ListQueryBuilder::<S3ObjectEntity>::new(&client);

        assert_eq!(builder.clone().count().await.unwrap(), 10);
        assert_eq!(builder.to_list_count().await.unwrap(), ListCount::new(10));
    }

    async fn paginate_all<T, M>(
        builder: ListQueryBuilder<'_, T>,
        page: u64,
        page_size: u64,
    ) -> Vec<M>
    where
        T: EntityTrait<Model = M>,
        M: FromQueryResult + Send + Sync,
    {
        builder
            .paginate(page, page_size)
            .await
            .unwrap()
            .all()
            .await
            .unwrap()
    }
}
