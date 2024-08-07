//! Query builder involving list operations on the database.
//!

use sea_orm::prelude::Expr;
use sea_orm::sea_query::extension::postgres::PgExpr;
use sea_orm::sea_query::{
    Alias, Asterisk, ColumnRef, IntoColumnRef, PostgresQueryBuilder, Query, SimpleExpr,
};
use sea_orm::Order::{Asc, Desc};
use sea_orm::{
    ActiveEnum, ColumnTrait, Condition, ConnectionTrait, EntityTrait, FromQueryResult,
    IntoSimpleExpr, JsonValue, PaginatorTrait, QueryFilter, QueryOrder, QuerySelect, QueryTrait,
    Select, Value,
};
use tracing::trace;

use crate::database::entities::{object, s3_object};
use crate::error::Error::OverflowError;
use crate::error::{Error, Result};
use crate::routes::filter::wildcard::WildcardEither;
use crate::routes::filter::{ObjectsFilter, S3ObjectsFilter};
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
    pub fn filter_condition(filter: ObjectsFilter, case_sensitive: bool) -> Condition {
        let mut condition = Condition::all();

        if let Some(attributes) = filter.attributes {
            let json_conditions = Self::json_conditions(
                object::Column::Attributes.into_column_ref(),
                attributes,
                case_sensitive,
            );
            for json_condition in json_conditions {
                condition = condition.add(json_condition);
            }
        }

        condition
    }

    /// Filter records by all fields in the filter variable.
    pub fn filter_all(mut self, filter: ObjectsFilter, case_sensitive: bool) -> Self {
        self.select = self
            .select
            .filter(Self::filter_condition(filter, case_sensitive));
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
    pub fn filter_all(mut self, filter: S3ObjectsFilter, case_sensitive: bool) -> Self {
        self.select = self
            .select
            .filter(Self::filter_condition(filter, case_sensitive));

        self.trace_query("filter_all");

        self
    }

    /// Create a condition to filter a query.
    pub fn filter_condition(filter: S3ObjectsFilter, case_sensitive: bool) -> Condition {
        let mut condition = Condition::all()
            .add_option(filter.event_type.map(|v| {
                Self::filter_operation(
                    Expr::col(s3_object::Column::EventType),
                    v.map(|or| or.as_enum()),
                    case_sensitive,
                )
            }))
            .add_option(filter.bucket.map(|v| {
                Self::filter_operation(
                    Expr::col(s3_object::Column::Bucket),
                    WildcardEither::Wildcard::<String>(v),
                    case_sensitive,
                )
            }))
            .add_option(filter.key.map(|v| {
                Self::filter_operation(
                    Expr::col(s3_object::Column::Key),
                    WildcardEither::Wildcard::<String>(v),
                    case_sensitive,
                )
            }))
            .add_option(filter.version_id.map(|v| {
                Self::filter_operation(
                    Expr::col(s3_object::Column::VersionId),
                    WildcardEither::Wildcard::<String>(v),
                    case_sensitive,
                )
            }))
            .add_option(filter.date.map(|v| {
                Self::filter_operation(Expr::col(s3_object::Column::Date), v, case_sensitive)
            }))
            .add_option(filter.size.map(|v| s3_object::Column::Size.eq(v)))
            .add_option(filter.sha256.map(|v| s3_object::Column::Sha256.eq(v)))
            .add_option(filter.last_modified_date.map(|v| {
                Self::filter_operation(
                    Expr::col(s3_object::Column::LastModifiedDate),
                    v,
                    case_sensitive,
                )
            }))
            .add_option(filter.e_tag.map(|v| s3_object::Column::ETag.eq(v)))
            .add_option(filter.storage_class.map(|v| {
                Self::filter_operation(
                    Expr::col(s3_object::Column::StorageClass),
                    v.map(|or| or.as_enum()),
                    case_sensitive,
                )
            }))
            .add_option(
                filter
                    .is_delete_marker
                    .map(|v| s3_object::Column::IsDeleteMarker.eq(v)),
            );

        if let Some(attributes) = filter.attributes {
            let json_conditions = Self::json_conditions(
                s3_object::Column::Attributes.into_column_ref(),
                attributes,
                case_sensitive,
            );
            for json_condition in json_conditions {
                condition = condition.add(json_condition);
            }
        }

        condition
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

    /// Create an operation based on the wildcard. This either results in a `like`/`ilike` or `=` comparison.
    pub fn filter_operation<S, W>(
        expr: S,
        wildcard: WildcardEither<W>,
        case_sensitive: bool,
    ) -> SimpleExpr
    where
        S: Into<SimpleExpr>,
        W: Into<SimpleExpr>,
    {
        let text_cast = Alias::new("text");
        let expr = expr.into();
        match wildcard {
            WildcardEither::Or(value) => expr.eq(value),
            WildcardEither::Wildcard(wildcard) => {
                if wildcard.contains_wildcard() && case_sensitive {
                    expr.cast_as(text_cast).like(wildcard.into_inner())
                } else if wildcard.contains_wildcard() && !case_sensitive {
                    expr.cast_as(text_cast).ilike(wildcard.into_inner())
                } else {
                    expr.eq(wildcard.into_inner())
                }
            }
        }
    }

    /// Add a json condition using equality and a concrete type.
    fn add_eq_condition<V>(
        acc: &mut Vec<SimpleExpr>,
        expr: SimpleExpr,
        value: V,
        case_sensitive: bool,
    ) where
        V: Into<Value>,
    {
        acc.push(Self::filter_operation(
            expr,
            WildcardEither::<V>::or(value),
            case_sensitive,
        ))
    }

    /// Add a json condition using like and a wildcard.
    fn add_like_condition(
        acc: &mut Vec<SimpleExpr>,
        expr: SimpleExpr,
        value: String,
        case_sensitive: bool,
    ) {
        acc.push(Self::filter_operation(
            expr,
            WildcardEither::<String>::wildcard(value),
            case_sensitive,
        ))
    }

    /// A recursive function to convert a json value to postgres ->> statements. This traverses the
    /// JSON tree and appends a list of conditions to `acc`. In practice, this should never
    /// produce more than one condition if using serde_qs because serde_qs should only parse one nested
    /// json object. However,  it is implemented fully here in case it is useful for JSON-based rules.
    fn apply_json_condition(
        acc: &mut Vec<SimpleExpr>,
        expr: SimpleExpr,
        json: JsonValue,
        case_sensitive: bool,
    ) {
        let mut traverse_expr = |cast_expr, v| {
            let expr = expr
                .clone()
                .cast_as(Alias::new("jsonb"))
                .cast_json_field(cast_expr);
            Self::apply_json_condition(acc, expr, v, case_sensitive)
        };

        match json {
            // Primitive types are compared for equality.
            v @ JsonValue::Null => Self::add_eq_condition(acc, expr, v, case_sensitive),
            JsonValue::Bool(v) => Self::add_eq_condition(acc, expr, v, case_sensitive),
            JsonValue::Number(v) => {
                if let Some(n) = v.as_f64() {
                    Self::add_eq_condition(acc, expr, n, case_sensitive)
                } else if let Some(n) = v.as_i64() {
                    Self::add_eq_condition(acc, expr, n, case_sensitive)
                } else if let Some(n) = v.as_u64() {
                    Self::add_eq_condition(acc, expr, n, case_sensitive)
                }
            }
            // Strings are compared as wildcards.
            JsonValue::String(v) => Self::add_like_condition(acc, expr, v, case_sensitive),
            // Arrays traverse with an index.
            JsonValue::Array(array) => {
                for (i, v) in array.into_iter().enumerate() {
                    traverse_expr(Expr::val(i as u32), v)
                }
            }
            // Objects traverse with a key.
            JsonValue::Object(o) => {
                for (k, v) in o.into_iter() {
                    traverse_expr(Expr::val(k), v)
                }
            }
        }
    }

    /// Create a series of json conditions by traversing the JSON tree.
    pub fn json_conditions(
        col: ColumnRef,
        json: JsonValue,
        case_sensitive: bool,
    ) -> Vec<SimpleExpr> {
        let mut conditions = vec![];
        let expr = Expr::col(col).into_simple_expr();

        Self::apply_json_condition(&mut conditions, expr, json, case_sensitive);

        conditions
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
pub(crate) mod tests {
    use sea_orm::prelude::Json;
    use sea_orm::sea_query::extension::postgres::PgBinOper;
    use sea_orm::sea_query::types::BinOper;
    use sea_orm::sea_query::IntoColumnRef;
    use sea_orm::DatabaseConnection;
    use serde_json::json;
    use sqlx::PgPool;

    use super::*;
    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::entities::sea_orm_active_enums::{EventType, StorageClass};
    use crate::database::Client;
    use crate::queries::update::tests::{change_many, entries_many, null_attributes};
    use crate::queries::EntriesBuilder;
    use crate::routes::filter::wildcard::Wildcard;

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
            .filter_all(
                S3ObjectsFilter {
                    size: Some(14),
                    ..Default::default()
                },
                true,
            );
        let result = builder.all().await.unwrap();
        assert_eq!(result, vec![entries[6].clone()]);

        // Order of filter call shouldn't matter.
        let builder = ListQueryBuilder::<_, s3_object::Entity>::new(client.connection_ref())
            .filter_all(
                S3ObjectsFilter {
                    size: Some(4),
                    ..Default::default()
                },
                true,
            )
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
            ObjectsFilter {
                attributes: Some(json!({
                    "attribute_id": "1"
                })),
            },
            true,
        )
        .await;
        assert_eq!(result, vec![entries[1].clone()]);

        let result = filter_all_objects_from(
            &client,
            ObjectsFilter {
                attributes: Some(json!({
                    "nested_id": {
                        "attribute_id": "1"
                    }
                })),
            },
            true,
        )
        .await;
        assert_eq!(result, vec![entries[1].clone()]);

        let result = filter_all_objects_from(
            &client,
            ObjectsFilter {
                attributes: Some(json!({
                    "non_existent_id": "1"
                })),
            },
            true,
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
            S3ObjectsFilter {
                event_type: Some(WildcardEither::Or(EventType::Created)),
                ..Default::default()
            },
            true,
        )
        .await;
        assert_eq!(result.len(), 5);
        assert_eq!(result, filter_event_type(entries, EventType::Created));
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
            S3ObjectsFilter {
                bucket: Some(Wildcard::new("0".to_string())),
                key: Some(Wildcard::new("1".to_string())),
                ..Default::default()
            },
            true,
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
            S3ObjectsFilter {
                attributes: Some(json!({
                    "attribute_id": "1"
                })),
                ..Default::default()
            },
            true,
        )
        .await;
        assert_eq!(result, vec![entries[1].clone()]);

        let result = filter_all_s3_objects_from(
            &client,
            S3ObjectsFilter {
                attributes: Some(json!({
                    "nested_id": {
                        "attribute_id": "2"
                    }
                })),
                ..Default::default()
            },
            true,
        )
        .await;
        assert_eq!(result, vec![entries[2].clone()]);

        let result = filter_all_s3_objects_from(
            &client,
            S3ObjectsFilter {
                attributes: Some(json!({
                    "non_existent_id": "1"
                })),
                ..Default::default()
            },
            true,
        )
        .await;
        assert!(result.is_empty());

        let result = filter_all_s3_objects_from(
            &client,
            S3ObjectsFilter {
                attributes: Some(json!({
                    "attribute_id": "1"
                })),
                key: Some(Wildcard::new("2".to_string())),
                ..Default::default()
            },
            true,
        )
        .await;
        assert!(result.is_empty());

        let result = filter_all_s3_objects_from(
            &client,
            S3ObjectsFilter {
                attributes: Some(json!({
                    "attribute_id": "3"
                })),
                key: Some(Wildcard::new("3".to_string())),
                ..Default::default()
            },
            true,
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

    #[test]
    fn test_filter_operation() {
        let operation = ListQueryBuilder::<DatabaseConnection, s3_object::Entity>::filter_operation(
            Expr::col(s3_object::Column::StorageClass),
            WildcardEither::Or(StorageClass::Standard),
            true,
        );
        assert!(matches!(
            operation,
            SimpleExpr::Binary(_, BinOper::Equal, _)
        ));

        let operation = ListQueryBuilder::<DatabaseConnection, s3_object::Entity>::filter_operation(
            Expr::col(s3_object::Column::StorageClass),
            WildcardEither::Or(StorageClass::Standard),
            false,
        );
        assert!(matches!(
            operation,
            SimpleExpr::Binary(_, BinOper::Equal, _)
        ));

        let operation = ListQueryBuilder::<DatabaseConnection, s3_object::Entity>::filter_operation(
            Expr::col(s3_object::Column::StorageClass),
            WildcardEither::Wildcard::<StorageClass>(Wildcard::new("Standar%".to_string())),
            true,
        );
        assert!(matches!(operation, SimpleExpr::Binary(_, BinOper::Like, _)));

        let operation = ListQueryBuilder::<DatabaseConnection, s3_object::Entity>::filter_operation(
            Expr::col(s3_object::Column::StorageClass),
            WildcardEither::Wildcard::<StorageClass>(Wildcard::new("Standar%".to_string())),
            false,
        );
        assert!(matches!(
            operation,
            SimpleExpr::Binary(_, BinOper::PgOperator(PgBinOper::ILike), _)
        ));
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_list_s3_objects_filter_wildcard(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(&client)
            .await;
        let s3_entries = entries.s3_objects.clone();

        let result = filter_all_s3_objects_from(
            &client,
            S3ObjectsFilter {
                event_type: Some(WildcardEither::Wildcard(Wildcard::new(
                    "Cr___ed".to_string(),
                ))),
                ..Default::default()
            },
            true,
        )
        .await;
        assert_eq!(
            result,
            filter_event_type(s3_entries.clone(), EventType::Created)
        );

        let result = filter_all_s3_objects_from(
            &client,
            S3ObjectsFilter {
                event_type: Some(WildcardEither::Wildcard(Wildcard::new(
                    "cr___ed".to_string(),
                ))),
                ..Default::default()
            },
            false,
        )
        .await;
        assert_eq!(
            result,
            filter_event_type(s3_entries.clone(), EventType::Created)
        );

        let result = filter_all_s3_objects_from(
            &client,
            S3ObjectsFilter {
                bucket: Some(Wildcard::new("0%".to_string())),
                ..Default::default()
            },
            false,
        )
        .await;
        assert_eq!(result, &s3_entries[0..2]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_list_s3_objects_wildcard_attributes(pool: PgPool) {
        let client = Client::from_pool(pool);
        let mut entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(&client)
            .await;

        let test_attributes = json!({
            "nested_id": {
                "attribute_id": "1"
            },
            "attribute_id": "test"
        });
        change_many(&client, &entries, &[0, 1], Some(test_attributes.clone())).await;
        change_many(
            &client,
            &entries,
            &(2..10).collect::<Vec<_>>(),
            Some(json!({
                "nested_id": {
                    "attribute_id": "test"
                },
                "attribute_id": "1"
            })),
        )
        .await;

        // Filter with wildcard attributes.
        let (objects, s3_objects) = filter_attributes(
            &client,
            Some(json!({
                "attribute_id": "t%"
            })),
            true,
        )
        .await;

        entries_many(&mut entries, &[0, 1], test_attributes);
        assert_eq!(objects, entries.objects[0..2].to_vec());
        assert_eq!(s3_objects, entries.s3_objects[0..2].to_vec());

        let test_attributes = json!({
            "attribute_id": "attribute_id"
        });
        change_many(&client, &entries, &[0, 1], Some(test_attributes.clone())).await;
        change_many(
            &client,
            &entries,
            &(2..10).collect::<Vec<_>>(),
            Some(json!({
                "nested_id": {
                    "attribute_id": "attribute_id"
                }
            })),
        )
        .await;

        entries_many(&mut entries, &[0, 1], test_attributes);

        let (objects, s3_objects) = filter_attributes(
            &client,
            Some(json!({
                // This should not trigger a fetch on the nested id.
                "attribute_id": "%a%"
            })),
            true,
        )
        .await;
        assert_eq!(objects, entries.objects[0..2].to_vec());
        assert_eq!(s3_objects, entries.s3_objects[0..2].to_vec());

        let (objects, s3_objects) = filter_attributes(
            &client,
            Some(json!({
                // Case-insensitive should work
                "attribute_id": "%A%"
            })),
            false,
        )
        .await;
        assert_eq!(objects, entries.objects[0..2].to_vec());
        assert_eq!(s3_objects, entries.s3_objects[0..2].to_vec());

        null_attributes(&client, &entries, 0).await;
        null_attributes(&client, &entries, 1).await;

        let (objects, s3_objects) = filter_attributes(
            &client,
            Some(json!({
                // A check is okay on null json as well.
                "attribute_id": "%1%"
            })),
            true,
        )
        .await;

        assert!(objects.is_empty());
        assert!(s3_objects.is_empty());
    }

    #[test]
    fn apply_json_condition() {
        let conditions = ListQueryBuilder::<DatabaseConnection, s3_object::Entity>::json_conditions(
            s3_object::Column::Attributes.into_column_ref(),
            json!({ "attribute_id": "1" }),
            true,
        );
        assert_eq!(conditions.len(), 1);

        let operation = conditions[0].clone();
        assert!(matches!(
            conditions[0].clone(),
            SimpleExpr::Binary(_, BinOper::Equal, _)
        ));
        assert_cast_json(&operation);

        let conditions = ListQueryBuilder::<DatabaseConnection, s3_object::Entity>::json_conditions(
            s3_object::Column::Attributes.into_column_ref(),
            json!({ "attribute_id": "a%" }),
            true,
        );
        assert_eq!(conditions.len(), 1);

        let operation = conditions[0].clone();
        assert!(matches!(operation, SimpleExpr::Binary(_, BinOper::Like, _)));
        assert_cast_json(&operation);

        let conditions = ListQueryBuilder::<DatabaseConnection, s3_object::Entity>::json_conditions(
            s3_object::Column::Attributes.into_column_ref(),
            json!({ "attribute_id": "a%" }),
            false,
        );
        assert_eq!(conditions.len(), 1);

        let operation = conditions[0].clone();
        assert!(matches!(
            operation,
            SimpleExpr::Binary(_, BinOper::PgOperator(PgBinOper::ILike), _)
        ));
        assert_cast_json(&operation);
    }

    fn assert_cast_json(operation: &SimpleExpr) {
        if let SimpleExpr::Binary(operation, _, _) = operation {
            if let SimpleExpr::FunctionCall(call) = operation.as_ref() {
                call.get_args().iter().for_each(assert_cast_json);
            } else {
                assert!(matches!(
                    operation.as_ref(),
                    SimpleExpr::Binary(_, BinOper::PgOperator(PgBinOper::CastJsonField), _)
                ));
            }
        }
    }

    pub(crate) fn filter_event_type(
        entries: Vec<s3_object::Model>,
        event_type: EventType,
    ) -> Vec<s3_object::Model> {
        entries
            .into_iter()
            .filter(|entry| entry.event_type == event_type)
            .collect::<Vec<_>>()
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

    async fn filter_attributes(
        client: &Client,
        filter: Option<Json>,
        case_sensitive: bool,
    ) -> (Vec<object::Model>, Vec<s3_object::Model>) {
        (
            filter_all_objects_from(
                client,
                ObjectsFilter {
                    attributes: filter.clone(),
                },
                case_sensitive,
            )
            .await,
            filter_all_s3_objects_from(
                client,
                S3ObjectsFilter {
                    attributes: filter,
                    ..Default::default()
                },
                case_sensitive,
            )
            .await,
        )
    }

    async fn filter_all_objects_from(
        client: &Client,
        filter: ObjectsFilter,
        case_sensitive: bool,
    ) -> Vec<object::Model> {
        ListQueryBuilder::<_, object::Entity>::new(client.connection_ref())
            .filter_all(filter, case_sensitive)
            .all()
            .await
            .unwrap()
    }

    async fn filter_all_s3_objects_from(
        client: &Client,
        filter: S3ObjectsFilter,
        case_sensitive: bool,
    ) -> Vec<s3_object::Model> {
        ListQueryBuilder::<_, s3_object::Entity>::new(client.connection_ref())
            .filter_all(filter, case_sensitive)
            .all()
            .await
            .unwrap()
    }
}
