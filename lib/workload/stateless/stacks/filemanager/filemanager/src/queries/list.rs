//! Query builder involving list operations on the database.
//!

use sea_orm::prelude::Expr;
use sea_orm::sea_query::extension::postgres::PgExpr;
use sea_orm::sea_query::{Alias, Asterisk, PostgresQueryBuilder, Query};
use sea_orm::Order::{Asc, Desc};
use sea_orm::{
    ColumnTrait, Condition, ConnectionTrait, EntityTrait, FromQueryResult, PaginatorTrait,
    QueryFilter, QueryOrder, QuerySelect, QueryTrait, Select,
};
use tracing::trace;

use crate::database::entities::{object, s3_object};
use crate::error::Error::OverflowError;
use crate::error::{Error, Result};
use crate::routes::filtering::{ObjectsFilterAll, S3ObjectsFilterAll};
use crate::routes::list::{ListCount, ListResponse};
use crate::routes::pagination::Pagination;

/// A query builder for list operations.
#[derive(Debug, Clone)]
pub struct ListQueryBuilder<'a, C, E>
where
    E: EntityTrait,
{
    connection: &'a C,
    select: Select<E>,
}

impl<'a, C> ListQueryBuilder<'a, C, object::Entity>
where
    C: ConnectionTrait,
{
    /// Create a new query builder.
    pub fn new(connection: &'a C) -> Self {
        Self {
            connection,
            select: Self::for_objects(),
        }
    }

    /// Define a select query for finding values from objects.
    pub fn for_objects() -> Select<object::Entity> {
        object::Entity::find()
    }

    /// Create a condition to filter a query.
    pub fn filter_condition(filter: ObjectsFilterAll) -> Condition {
        Condition::all().add_option(
            filter
                .attributes
                .map(|v| Expr::col(object::Column::Attributes).contains(v)),
        )
    }

    /// Filter records by all fields in the filter variable.
    pub fn filter_all(mut self, filter: ObjectsFilterAll) -> Self {
        self.select = self.select.filter(Self::filter_condition(filter));
        self
    }
}

impl<'a, C> ListQueryBuilder<'a, C, s3_object::Entity>
where
    C: ConnectionTrait,
{
    /// Create a new query builder.
    pub fn new(connection: &'a C) -> Self {
        Self {
            connection,
            select: Self::for_s3_objects(),
        }
    }

    /// Define a select query for finding values from s3 objects.
    pub fn for_s3_objects() -> Select<s3_object::Entity> {
        s3_object::Entity::find().order_by_asc(s3_object::Column::Sequencer)
    }

    /// Filter records by all fields in the filter variable.
    ///
    /// This creates a query which is similar to:
    ///
    /// ```sql
    /// select * from s3_object
    /// where event_type = filter.event_type and
    ///     bucket = filter.bucket and
    ///     ...;
    /// ```
    pub fn filter_all(mut self, filter: S3ObjectsFilterAll) -> Self {
        self.select = self.select.filter(Self::filter_condition(filter));

        self.trace_query("filter_all");

        self
    }

    /// Create a condition to filter a query.
    pub fn filter_condition(filter: S3ObjectsFilterAll) -> Condition {
        Condition::all()
            .add_option(
                filter
                    .event_type
                    .map(|v| s3_object::Column::EventType.eq(v)),
            )
            .add_option(filter.bucket.map(|v| s3_object::Column::Bucket.eq(v)))
            .add_option(filter.key.map(|v| s3_object::Column::Key.eq(v)))
            .add_option(
                filter
                    .version_id
                    .map(|v| s3_object::Column::VersionId.eq(v)),
            )
            .add_option(filter.date.map(|v| s3_object::Column::Date.eq(v)))
            .add_option(filter.size.map(|v| s3_object::Column::Size.eq(v)))
            .add_option(filter.sha256.map(|v| s3_object::Column::Sha256.eq(v)))
            .add_option(
                filter
                    .last_modified_date
                    .map(|v| s3_object::Column::LastModifiedDate.eq(v)),
            )
            .add_option(filter.e_tag.map(|v| s3_object::Column::ETag.eq(v)))
            .add_option(
                filter
                    .storage_class
                    .map(|v| s3_object::Column::StorageClass.eq(v)),
            )
            .add_option(
                filter
                    .is_delete_marker
                    .map(|v| s3_object::Column::IsDeleteMarker.eq(v)),
            )
            .add_option(
                filter
                    .attributes
                    .map(|v| Expr::col(s3_object::Column::Attributes).contains(v)),
            )
    }

    /// Update this query to find objects that represent the current state of S3 objects. That is,
    /// this gets all non-deleted objects. This means that only `Created` events will be returned,
    /// and these will be the most up to date at this point, without any 'Deleted' events coming
    /// after them.
    ///
    /// This creates a query which is roughly equivalent to the following:
    ///
    /// ```sql
    /// select * from (
    ///     select distinct on (bucket, key, version_id) * from s3_object
    ///     order by bucket, key, version_id, sequencer desc
    /// ) as s3_object
    /// where event_type = 'Created';
    /// ```
    ///
    /// This finds all distinct objects within a (bucket, key, version_id) grouping such that they
    /// are most recent and only `Created` events.
    pub fn current_state(mut self) -> Self {
        let subquery = Query::select()
            .column(Asterisk)
            .distinct_on([
                s3_object::Column::Bucket,
                s3_object::Column::Key,
                s3_object::Column::VersionId,
            ])
            .from(s3_object::Entity)
            .order_by_columns([
                (s3_object::Column::Bucket, Asc),
                (s3_object::Column::Key, Asc),
                (s3_object::Column::VersionId, Asc),
                (s3_object::Column::Sequencer, Desc),
            ])
            .take();

        // Clear the current from state (which should be `from s3_object`), and
        // Update it to the distinct_on subquery.
        QuerySelect::query(&mut self.select)
            .from_clear()
            .from_subquery(subquery, Alias::new("s3_object"))
            .and_where(s3_object::Column::EventType.eq("Created"));

        self.trace_query("current_state");

        self
    }
}

impl<'a, C, E> From<(&'a C, Select<E>)> for ListQueryBuilder<'a, C, E>
where
    C: ConnectionTrait,
    E: EntityTrait,
{
    fn from((connection, select): (&'a C, Select<E>)) -> Self {
        Self { connection, select }
    }
}

impl<'a, C, E> ListQueryBuilder<'a, C, E>
where
    C: ConnectionTrait,
    E: EntityTrait,
{
    /// Get the inner connection and select statement.
    pub fn into_inner(self) -> (&'a C, Select<E>) {
        (self.connection, self.select)
    }

    /// Get a copy of this query builder
    pub fn cloned(&self) -> Self {
        (self.connection, self.select.clone()).into()
    }
}

impl<'a, C, E, M> ListQueryBuilder<'a, C, E>
where
    C: ConnectionTrait,
    E: EntityTrait<Model = M>,
    M: FromQueryResult + Send + Sync,
{
    /// Execute the prepared query, fetching all values.
    pub async fn all(self) -> Result<Vec<M>> {
        Ok(self.select.all(self.connection).await?)
    }

    /// Execute the prepared query, fetching one value.
    pub async fn one(self) -> Result<Option<M>> {
        Ok(self.select.one(self.connection).await?)
    }

    /// Execute the prepared query, counting all values.
    pub async fn count(self) -> Result<u64> {
        Ok(self.select.count(self.connection).await?)
    }

    /// Paginate the query for the given page and page_size.
    ///
    /// This produces a query similar to:
    ///
    /// ```sql
    /// select * from s3_object
    ///     limit page_size
    ///     offset page * page_size;
    /// ```
    pub async fn paginate(mut self, page: u64, page_size: u64) -> Result<Self> {
        let offset = page.checked_mul(page_size).ok_or_else(|| OverflowError)?;
        self.select = self.select.offset(offset).limit(page_size);

        self.trace_query("paginate");

        Ok(self)
    }

    /// Create a list response from pagination query parameters and a query builder.
    pub async fn paginate_to_list_response(
        self,
        pagination: Pagination,
    ) -> Result<ListResponse<M>> {
        let page = pagination.page();
        let page_size = pagination.page_size();
        let mut query = self.paginate(page, page_size).await?;

        // Always add one to the limit to see if there is additional pages that can be fetched.
        QuerySelect::query(&mut query.select).reset_limit();
        query.select = query
            .select
            .limit(page_size.checked_add(1).ok_or_else(|| OverflowError)?);

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

    /// Trace the current query.
    pub fn trace_query(&self, message: &str) {
        trace!(
            "{message}: {}",
            self.select.as_query().to_string(PostgresQueryBuilder)
        );
    }
}

#[cfg(test)]
mod tests {
    use serde_json::json;
    use sqlx::PgPool;

    use super::*;
    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::entities::sea_orm_active_enums::EventType;
    use crate::database::Client;
    use crate::queries::EntriesBuilder;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_list_objects(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = EntriesBuilder::default().build(&client).await.objects;

        let builder = ListQueryBuilder::<_, object::Entity>::new(client.connection_ref());
        let result = builder.all().await.unwrap();

        assert_eq!(result, entries);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_current_s3_objects_10(pool: PgPool) {
        let client = Client::from_pool(pool);

        let entries = EntriesBuilder::default()
            .with_bucket_divisor(4)
            .with_key_divisor(3)
            .with_shuffle(true)
            .build(&client)
            .await
            .s3_objects;
        let builder =
            ListQueryBuilder::<_, s3_object::Entity>::new(client.connection_ref()).current_state();
        let result = builder.all().await.unwrap();

        assert_eq!(result, vec![entries[2].clone(), entries[8].clone()]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_current_s3_objects_30(pool: PgPool) {
        let client = Client::from_pool(pool);

        let entries = EntriesBuilder::default()
            .with_n(30)
            .with_bucket_divisor(8)
            .with_key_divisor(5)
            .with_shuffle(true)
            .build(&client)
            .await
            .s3_objects;
        let builder =
            ListQueryBuilder::<_, s3_object::Entity>::new(client.connection_ref()).current_state();
        let result = builder.all().await.unwrap();

        assert_eq!(
            result,
            vec![entries[6].clone(), entries[17].clone(), entries[24].clone()]
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_current_s3_objects_with_paginate_10(pool: PgPool) {
        let client = Client::from_pool(pool);

        let entries = EntriesBuilder::default()
            .with_bucket_divisor(4)
            .with_key_divisor(3)
            .with_shuffle(true)
            .build(&client)
            .await
            .s3_objects;

        let builder = ListQueryBuilder::<_, s3_object::Entity>::new(client.connection_ref())
            .current_state()
            .paginate(0, 1)
            .await
            .unwrap();
        let result = builder.all().await.unwrap();
        assert_eq!(result, vec![entries[2].clone()]);

        // Order of paginate call shouldn't matter.
        let builder = ListQueryBuilder::<_, s3_object::Entity>::new(client.connection_ref())
            .paginate(1, 1)
            .await
            .unwrap()
            .current_state();
        let result = builder.all().await.unwrap();
        assert_eq!(result, vec![entries[8].clone()]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_current_s3_objects_with_filter(pool: PgPool) {
        let client = Client::from_pool(pool);

        let entries = EntriesBuilder::default()
            .with_n(30)
            .with_bucket_divisor(8)
            .with_key_divisor(5)
            .with_shuffle(true)
            .build(&client)
            .await
            .s3_objects;

        let builder = ListQueryBuilder::<_, s3_object::Entity>::new(client.connection_ref())
            .current_state()
            .filter_all(S3ObjectsFilterAll {
                size: Some(14),
                ..Default::default()
            });
        let result = builder.all().await.unwrap();
        assert_eq!(result, vec![entries[6].clone()]);

        // Order of filter call shouldn't matter.
        let builder = ListQueryBuilder::<_, s3_object::Entity>::new(client.connection_ref())
            .filter_all(S3ObjectsFilterAll {
                size: Some(4),
                ..Default::default()
            })
            .current_state();
        let result = builder.all().await.unwrap();
        assert_eq!(result, vec![entries[24].clone()]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_list_objects_filter_attributes(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = EntriesBuilder::default().build(&client).await.objects;

        let result = filter_all_objects_from(
            &client,
            ObjectsFilterAll {
                attributes: Some(json!({
                    "attribute_id": "1"
                })),
            },
        )
        .await;
        assert_eq!(result, vec![entries[1].clone()]);

        let result = filter_all_objects_from(
            &client,
            ObjectsFilterAll {
                attributes: Some(json!({
                    "nested_id": {
                        "attribute_id": "1"
                    }
                })),
            },
        )
        .await;
        assert_eq!(result, vec![entries[1].clone()]);

        let result = filter_all_objects_from(
            &client,
            ObjectsFilterAll {
                attributes: Some(json!({
                    "non_existent_id": "1"
                })),
            },
        )
        .await;
        assert!(result.is_empty());
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_paginate_objects(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = EntriesBuilder::default().build(&client).await.objects;

        let builder = ListQueryBuilder::<_, object::Entity>::new(client.connection_ref());

        let result = paginate_all(builder.clone(), 3, 3).await;
        assert_eq!(result, entries[9..]);
        // Empty result when paginating above the collection size.
        assert!(paginate_all(builder.clone(), 10, 2).await.is_empty());

        let result = builder
            .paginate_to_list_response(Pagination::new(0, 2))
            .await
            .unwrap();

        assert_eq!(result.next_page(), Some(1));
        assert_eq!(result.results(), &entries[0..2]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_list_s3_objects(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(&client)
            .await
            .s3_objects;

        let builder = ListQueryBuilder::<_, s3_object::Entity>::new(client.connection_ref());
        let result = builder.all().await.unwrap();

        assert_eq!(result, entries);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_list_s3_objects_filter_event_type(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(&client)
            .await
            .s3_objects;

        let result = filter_all_s3_objects_from(
            &client,
            S3ObjectsFilterAll {
                event_type: Some(EventType::Created),
                ..Default::default()
            },
        )
        .await;
        assert_eq!(result.len(), 5);
        assert_eq!(
            result,
            entries
                .into_iter()
                .filter(|entry| entry.event_type == EventType::Created)
                .collect::<Vec<_>>()
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_list_s3_objects_multiple_filters(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(&client)
            .await
            .s3_objects;

        let result = filter_all_s3_objects_from(
            &client,
            S3ObjectsFilterAll {
                bucket: Some("0".to_string()),
                key: Some("1".to_string()),
                ..Default::default()
            },
        )
        .await;
        assert_eq!(result, vec![entries[1].clone()]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_list_s3_objects_filter_attributes(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(&client)
            .await
            .s3_objects;

        let result = filter_all_s3_objects_from(
            &client,
            S3ObjectsFilterAll {
                attributes: Some(json!({
                    "attribute_id": "1"
                })),
                ..Default::default()
            },
        )
        .await;
        assert_eq!(result, vec![entries[1].clone()]);

        let result = filter_all_s3_objects_from(
            &client,
            S3ObjectsFilterAll {
                attributes: Some(json!({
                    "nested_id": {
                        "attribute_id": "2"
                    }
                })),
                ..Default::default()
            },
        )
        .await;
        assert_eq!(result, vec![entries[2].clone()]);

        let result = filter_all_s3_objects_from(
            &client,
            S3ObjectsFilterAll {
                attributes: Some(json!({
                    "non_existent_id": "1"
                })),
                ..Default::default()
            },
        )
        .await;
        assert!(result.is_empty());

        let result = filter_all_s3_objects_from(
            &client,
            S3ObjectsFilterAll {
                attributes: Some(json!({
                    "attribute_id": "1"
                })),
                key: Some("2".to_string()),
                ..Default::default()
            },
        )
        .await;
        assert!(result.is_empty());

        let result = filter_all_s3_objects_from(
            &client,
            S3ObjectsFilterAll {
                attributes: Some(json!({
                    "attribute_id": "3"
                })),
                key: Some("3".to_string()),
                ..Default::default()
            },
        )
        .await;
        assert_eq!(result, vec![entries[3].clone()]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_paginate_s3_objects(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(&client)
            .await
            .s3_objects;

        let builder = ListQueryBuilder::<_, s3_object::Entity>::new(client.connection_ref());

        let result = paginate_all(builder.clone(), 3, 3).await;
        assert_eq!(result, entries[9..]);
        // Empty result when paginating above the collection size.
        assert!(paginate_all(builder.clone(), 10, 2).await.is_empty());

        let result = builder
            .paginate_to_list_response(Pagination::new(0, 2))
            .await
            .unwrap();

        assert_eq!(result.next_page(), Some(1));
        assert_eq!(result.results(), &entries[0..2]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_count_objects(pool: PgPool) {
        let client = Client::from_pool(pool);
        EntriesBuilder::default()
            .with_shuffle(true)
            .build(&client)
            .await;

        let builder = ListQueryBuilder::<_, object::Entity>::new(client.connection_ref());

        assert_eq!(builder.clone().count().await.unwrap(), 10);
        assert_eq!(builder.to_list_count().await.unwrap(), ListCount::new(10));
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_count_s3_objects(pool: PgPool) {
        let client = Client::from_pool(pool);
        EntriesBuilder::default()
            .with_shuffle(true)
            .build(&client)
            .await;

        let builder = ListQueryBuilder::<_, s3_object::Entity>::new(client.connection_ref());

        assert_eq!(builder.clone().count().await.unwrap(), 10);
        assert_eq!(builder.to_list_count().await.unwrap(), ListCount::new(10));
    }

    async fn paginate_all<C, T, M>(
        builder: ListQueryBuilder<'_, C, T>,
        page: u64,
        page_size: u64,
    ) -> Vec<M>
    where
        T: EntityTrait<Model = M>,
        C: ConnectionTrait,
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

    async fn filter_all_objects_from(
        client: &Client,
        filter: ObjectsFilterAll,
    ) -> Vec<object::Model> {
        ListQueryBuilder::<_, object::Entity>::new(client.connection_ref())
            .filter_all(filter)
            .all()
            .await
            .unwrap()
    }

    async fn filter_all_s3_objects_from(
        client: &Client,
        filter: S3ObjectsFilterAll,
    ) -> Vec<s3_object::Model> {
        ListQueryBuilder::<_, s3_object::Entity>::new(client.connection_ref())
            .filter_all(filter)
            .all()
            .await
            .unwrap()
    }
}
