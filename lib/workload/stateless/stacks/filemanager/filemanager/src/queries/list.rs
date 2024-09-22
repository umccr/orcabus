//! Query builder involving list operations on the database.
//!

use sea_orm::prelude::Expr;
use sea_orm::sea_query::extension::postgres::PgExpr;
use sea_orm::sea_query::{
    Alias, Asterisk, BinOper, ColumnRef, IntoColumnRef, PostgresQueryBuilder, Query, SimpleExpr,
};
use sea_orm::Order::{Asc, Desc};
use sea_orm::{
    ColumnTrait, Condition, ConnectionTrait, EntityTrait, FromQueryResult, IntoSimpleExpr,
    JsonValue, PaginatorTrait, QueryFilter, QueryOrder, QuerySelect, QueryTrait, Select,
};
use tracing::trace;
use url::Url;

use crate::database::entities::s3_object;
use crate::error::Error::OverflowError;
use crate::error::{Error, Result};
use crate::routes::filter::wildcard::{Wildcard, WildcardEither};
use crate::routes::filter::S3ObjectsFilter;
use crate::routes::list::ListCount;
use crate::routes::pagination::{ListResponse, Pagination};

/// A query builder for list operations.
#[derive(Debug, Clone)]
pub struct ListQueryBuilder<'a, C, E>
where
    E: EntityTrait,
{
    connection: &'a C,
    select: Select<E>,
}

impl<'a, C> ListQueryBuilder<'a, C, s3_object::Entity>
where
    C: ConnectionTrait,
{
    /// Create a new query builder.
    pub fn new(connection: &'a C) -> Self {
        Self {
            connection,
            select: Self::for_s3(),
        }
    }

    /// Define a select query for finding values from s3 objects.
    pub fn for_s3() -> Select<s3_object::Entity> {
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
    pub fn filter_all(mut self, filter: S3ObjectsFilter, case_sensitive: bool) -> Result<Self> {
        self.select = self
            .select
            .filter(Self::filter_condition(filter, case_sensitive)?);

        self.trace_query("filter_all");

        Ok(self)
    }

    /// Create a condition to filter a query.
    pub fn filter_condition(filter: S3ObjectsFilter, case_sensitive: bool) -> Result<Condition> {
        let mut condition = Condition::all()
            .add_option(
                filter
                    .event_type
                    .map(|v| s3_object::Column::EventType.eq(v)),
            )
            .add_option(
                filter
                    .bucket
                    .map(|v| {
                        Self::filter_operation(
                            Expr::col(s3_object::Column::Bucket),
                            WildcardEither::Wildcard::<String>(v),
                            case_sensitive,
                        )
                    })
                    .transpose()?,
            )
            .add_option(
                filter
                    .key
                    .map(|v| {
                        Self::filter_operation(
                            Expr::col(s3_object::Column::Key),
                            WildcardEither::Wildcard::<String>(v),
                            case_sensitive,
                        )
                    })
                    .transpose()?,
            )
            .add_option(
                filter
                    .version_id
                    .map(|v| {
                        Self::filter_operation(
                            Expr::col(s3_object::Column::VersionId),
                            WildcardEither::Wildcard::<String>(v),
                            case_sensitive,
                        )
                    })
                    .transpose()?,
            )
            .add_option(
                filter
                    .event_time
                    .map(|v| {
                        Self::filter_operation(
                            Expr::col(s3_object::Column::EventTime),
                            v,
                            case_sensitive,
                        )
                    })
                    .transpose()?,
            )
            .add_option(filter.size.map(|v| s3_object::Column::Size.eq(v)))
            .add_option(filter.sha256.map(|v| s3_object::Column::Sha256.eq(v)))
            .add_option(
                filter
                    .last_modified_date
                    .map(|v| {
                        Self::filter_operation(
                            Expr::col(s3_object::Column::LastModifiedDate),
                            v,
                            case_sensitive,
                        )
                    })
                    .transpose()?,
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
            );

        if let Some(attributes) = filter.attributes {
            let json_conditions = Self::json_conditions(
                s3_object::Column::Attributes.into_column_ref(),
                attributes,
                case_sensitive,
            )?;

            for json_condition in json_conditions {
                condition = condition.add(json_condition);
            }
        }

        Ok(condition)
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
    /// where event_type = 'Created' and is_delete_marker = false;
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
            .and_where(s3_object::Column::EventType.eq("Created"))
            .and_where(s3_object::Column::IsDeleteMarker.eq(false));

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
    pub async fn paginate(mut self, offset: u64, page_size: u64) -> Result<Self> {
        let offset = offset.checked_mul(page_size).ok_or_else(|| OverflowError)?;
        self.select = self.select.offset(offset).limit(page_size);

        self.trace_query("paginate");

        Ok(self)
    }

    /// Create a list response from pagination query parameters and a query builder.
    pub async fn paginate_to_list_response(
        self,
        pagination: Pagination,
        page_link: Url,
        count: u64,
    ) -> Result<ListResponse<M>> {
        let offset = pagination.offset()?;
        let page_size = pagination.rows_per_page();
        let mut query = self.paginate(offset, page_size).await?;

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
            Some(
                pagination
                    .page()
                    .checked_add(1)
                    .ok_or_else(|| OverflowError)?,
            )
        };

        ListResponse::from_next_page(pagination, results, next_page, page_link, count)
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
    ) -> Result<SimpleExpr>
    where
        S: Into<SimpleExpr>,
        W: Into<SimpleExpr>,
    {
        let text_cast = Alias::new("text");
        let expr = expr.into();
        match wildcard {
            WildcardEither::Or(value) => Ok(expr.eq(value)),
            WildcardEither::Wildcard(wildcard) => {
                if wildcard.contains_wildcard() && case_sensitive {
                    Ok(expr.cast_as(text_cast).like(wildcard.to_like_expression()?))
                } else if wildcard.contains_wildcard() && !case_sensitive {
                    Ok(expr
                        .cast_as(text_cast)
                        .ilike(wildcard.to_like_expression()?))
                } else {
                    Ok(expr.eq(wildcard.to_eq_expression()?))
                }
            }
        }
    }

    /// A recursive function to convert a json value to postgres ->> statements. This traverses the
    /// JSON tree and appends a list of conditions to `acc`. In practice, this should never
    /// produce more than one condition if using serde_qs because serde_qs should only parse one nested
    /// json object. However,  it is implemented fully here in case it is useful for JSON-based rules.
    fn construct_json_path(
        acc: &mut Vec<String>,
        current: &mut String,
        json: JsonValue,
        case_sensitive: bool,
    ) -> Result<()> {
        let mut traverse_expr = |current: &mut String, traverse, next| {
            current.push_str(&format!(".{traverse}"));
            Self::construct_json_path(acc, current, next, case_sensitive)
        };
        let add_eq_condition = |acc: &mut Vec<String>, current: &mut String, v| {
            current.push_str(&format!(" ? (@ == {v})"));
            acc.push(current.to_string());
        };
        let add_like_condition = |acc: &mut Vec<String>, current: &mut String, v| {
            if !case_sensitive {
                current.push_str(&format!(" ? (@ like_regex \"{v}\" flag \"i\")"));
            } else {
                current.push_str(&format!(" ? (@ like_regex \"{v}\")"));
            }
            acc.push(current.to_string());
        };

        match json {
            // Primitive types are compared for equality.
            v @ JsonValue::Null => add_eq_condition(acc, current, v.to_string()),
            JsonValue::Bool(v) => add_eq_condition(acc, current, v.to_string()),
            JsonValue::Number(v) => {
                if let Some(n) = v.as_f64() {
                    add_eq_condition(acc, current, n.to_string());
                } else if let Some(n) = v.as_i64() {
                    add_eq_condition(acc, current, n.to_string());
                } else if let Some(n) = v.as_u64() {
                    add_eq_condition(acc, current, n.to_string());
                }
            }
            // Strings are compared as wildcards.
            JsonValue::String(v) => {
                let wildcard = Wildcard::new(v);
                if wildcard.contains_wildcard() {
                    let like_regex = wildcard.to_like_regex()?;
                    add_like_condition(acc, current, like_regex);
                } else {
                    // Extra quotes needed for JSON strings.
                    add_eq_condition(
                        acc,
                        current,
                        format!("\"{}\"", wildcard.to_eq_expression()?),
                    );
                }
            }
            // Arrays traverse with an index.
            JsonValue::Array(array) => {
                for (i, v) in array.into_iter().enumerate() {
                    traverse_expr(current, i.to_string(), v)?;
                }
            }
            // Objects traverse with a key.
            JsonValue::Object(o) => {
                for (k, v) in o.into_iter() {
                    traverse_expr(current, k.to_string(), v)?;
                }
            }
        }

        Ok(())
    }

    /// Create a series of json conditions by traversing the JSON tree.
    pub fn json_conditions(
        col: ColumnRef,
        json: JsonValue,
        case_sensitive: bool,
    ) -> Result<Vec<SimpleExpr>> {
        let mut conditions = vec![];

        let mut acc = "$".to_string();
        Self::construct_json_path(&mut conditions, &mut acc, json, case_sensitive)?;

        Ok(conditions
            .into_iter()
            .map(|cond| {
                let cond = Expr::val(cond).cast_as(Alias::new("jsonpath"));
                Expr::col(col.clone())
                    .into_simple_expr()
                    .binary(BinOper::Custom("@?"), cond)
            })
            .collect())
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
    use sea_orm::sea_query::SimpleExpr::Binary;
    use sea_orm::DatabaseConnection;
    use serde_json::json;
    use sqlx::PgPool;

    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::entities::sea_orm_active_enums::{EventType, StorageClass};
    use crate::database::Client;
    use crate::queries::update::tests::{change_many, entries_many, null_attributes};
    use crate::queries::EntriesBuilder;
    use crate::routes::filter::wildcard::Wildcard;
    use crate::routes::pagination::Links;

    use super::*;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_current_s3(pool: PgPool) {
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
    async fn test_current_s3_large_n(pool: PgPool) {
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
    async fn test_current_s3_with_paginate(pool: PgPool) {
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
    async fn test_current_s3_with_filter(pool: PgPool) {
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
            )
            .unwrap();
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
            .unwrap()
            .current_state();
        let result = builder.all().await.unwrap();
        assert_eq!(result, vec![entries[24].clone()]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_list_s3(pool: PgPool) {
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
    async fn test_list_s3_filter_event_type(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(&client)
            .await
            .s3_objects;

        let result = filter_all_s3_from(
            &client,
            S3ObjectsFilter {
                event_type: Some(EventType::Created),
                ..Default::default()
            },
            true,
        )
        .await;
        assert_eq!(result.len(), 5);
        assert_eq!(result, filter_event_type(entries, EventType::Created));
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_list_s3_multiple_filters(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(&client)
            .await
            .s3_objects;

        let result = filter_all_s3_from(
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
    async fn test_list_s3_filter_attributes(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(&client)
            .await
            .s3_objects;

        let result = filter_all_s3_from(
            &client,
            S3ObjectsFilter {
                attributes: Some(json!({
                    "attributeId": "1"
                })),
                ..Default::default()
            },
            true,
        )
        .await;
        assert_eq!(result, vec![entries[1].clone()]);

        let result = filter_all_s3_from(
            &client,
            S3ObjectsFilter {
                attributes: Some(json!({
                    "nestedId": {
                        "attributeId": "2"
                    }
                })),
                ..Default::default()
            },
            true,
        )
        .await;
        assert_eq!(result, vec![entries[2].clone()]);

        let result = filter_all_s3_from(
            &client,
            S3ObjectsFilter {
                attributes: Some(json!({
                    "nonExistentId": "1"
                })),
                ..Default::default()
            },
            true,
        )
        .await;
        assert!(result.is_empty());

        let result = filter_all_s3_from(
            &client,
            S3ObjectsFilter {
                attributes: Some(json!({
                    "attributeId": "1"
                })),
                key: Some(Wildcard::new("2".to_string())),
                ..Default::default()
            },
            true,
        )
        .await;
        assert!(result.is_empty());

        let result = filter_all_s3_from(
            &client,
            S3ObjectsFilter {
                attributes: Some(json!({
                    "attributeId": "3"
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
    async fn test_paginate_s3(pool: PgPool) {
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
            .paginate_to_list_response(
                Pagination::from_u64(1, 2).unwrap(),
                "http://example.com/s3?rowsPerPage=2&page=1"
                    .parse()
                    .unwrap(),
                10,
            )
            .await
            .unwrap();

        assert_eq!(
            result.links(),
            &Links::new(
                None,
                Some(
                    "http://example.com/s3?rowsPerPage=2&page=2"
                        .parse()
                        .unwrap()
                )
            )
        );
        assert_eq!(result.results(), &entries[0..2]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_count_s3(pool: PgPool) {
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
        let operation =
            ListQueryBuilder::<DatabaseConnection, s3_object::Entity>::filter_operation(
                Expr::col(s3_object::Column::StorageClass),
                WildcardEither::Or(StorageClass::Standard),
                true,
            )
            .unwrap();
        assert!(matches!(
            operation,
            SimpleExpr::Binary(_, BinOper::Equal, _)
        ));

        let operation =
            ListQueryBuilder::<DatabaseConnection, s3_object::Entity>::filter_operation(
                Expr::col(s3_object::Column::StorageClass),
                WildcardEither::Or(StorageClass::Standard),
                false,
            )
            .unwrap();
        assert!(matches!(
            operation,
            SimpleExpr::Binary(_, BinOper::Equal, _)
        ));

        let operation =
            ListQueryBuilder::<DatabaseConnection, s3_object::Entity>::filter_operation(
                Expr::col(s3_object::Column::StorageClass),
                WildcardEither::Wildcard::<StorageClass>(Wildcard::new("Standar*".to_string())),
                true,
            )
            .unwrap();
        assert!(matches!(operation, SimpleExpr::Binary(_, BinOper::Like, _)));

        let operation =
            ListQueryBuilder::<DatabaseConnection, s3_object::Entity>::filter_operation(
                Expr::col(s3_object::Column::StorageClass),
                WildcardEither::Wildcard::<StorageClass>(Wildcard::new("Standar*".to_string())),
                false,
            )
            .unwrap();
        assert!(matches!(
            operation,
            SimpleExpr::Binary(_, BinOper::PgOperator(PgBinOper::ILike), _)
        ));
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_list_s3_filter_wildcard(pool: PgPool) {
        let client = Client::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(&client)
            .await;
        let s3_entries = entries.s3_objects.clone();

        let result = filter_all_s3_from(
            &client,
            S3ObjectsFilter {
                event_time: Some(WildcardEither::Wildcard(Wildcard::new(
                    "1970-01-0*".to_string(),
                ))),
                ..Default::default()
            },
            true,
        )
        .await;
        assert_eq!(
            result,
            s3_entries
                .clone()
                .into_iter()
                .filter(|entry| entry
                    .event_time
                    .unwrap()
                    .to_string()
                    .starts_with("1970-01-0"))
                .collect::<Vec<_>>()
        );

        let result = filter_all_s3_from(
            &client,
            S3ObjectsFilter {
                bucket: Some(Wildcard::new("0*".to_string())),
                ..Default::default()
            },
            false,
        )
        .await;
        assert_eq!(result, &s3_entries[0..2]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_list_s3_wildcard_attributes(pool: PgPool) {
        let client = Client::from_pool(pool);
        let mut entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(&client)
            .await;

        let test_attributes = json!({
            "nestedId": {
                "attributeId": "1"
            },
            "attributeId": "test"
        });
        change_many(&client, &entries, &[0, 1], Some(test_attributes.clone())).await;
        change_many(
            &client,
            &entries,
            &(2..10).collect::<Vec<_>>(),
            Some(json!({
                "nestedId": {
                    "attributeId": "test"
                },
                "attributeId": "1"
            })),
        )
        .await;

        // Filter with wildcard attributes.
        let s3_objects = filter_attributes(
            &client,
            Some(json!({
                "attributeId": "t*"
            })),
            true,
        )
        .await;

        entries_many(&mut entries, &[0, 1], test_attributes);
        assert_eq!(s3_objects, entries.s3_objects[0..2].to_vec());

        let test_attributes = json!({
            "attributeId": "attributeId"
        });
        change_many(&client, &entries, &[0, 1], Some(test_attributes.clone())).await;
        change_many(
            &client,
            &entries,
            &(2..10).collect::<Vec<_>>(),
            Some(json!({
                "nestedId": {
                    "attributeId": "attributeId"
                }
            })),
        )
        .await;

        entries_many(&mut entries, &[0, 1], test_attributes);

        let s3_objects = filter_attributes(
            &client,
            Some(json!({
                // This should not trigger a fetch on the nested id.
                "attributeId": "*a*"
            })),
            true,
        )
        .await;
        assert_eq!(s3_objects, entries.s3_objects[0..2].to_vec());

        let s3_objects = filter_attributes(
            &client,
            Some(json!({
                // Case-insensitive should work
                "attributeId": "*A*"
            })),
            false,
        )
        .await;
        assert_eq!(s3_objects, entries.s3_objects[0..2].to_vec());

        null_attributes(&client, &entries, 0).await;
        null_attributes(&client, &entries, 1).await;

        let s3_objects = filter_attributes(
            &client,
            Some(json!({
                // A check is okay on null json as well.
                "attributeId": "*1*"
            })),
            true,
        )
        .await;

        assert!(s3_objects.is_empty());
    }

    #[test]
    fn apply_json_condition() {
        let conditions =
            ListQueryBuilder::<DatabaseConnection, s3_object::Entity>::json_conditions(
                s3_object::Column::Attributes.into_column_ref(),
                json!({ "attributeId": "1" }),
                true,
            )
            .unwrap();
        assert_eq!(conditions.len(), 1);

        let operation = conditions[0].clone();
        assert!(matches!(
            operation,
            SimpleExpr::Binary(_, BinOper::Custom("@?"), _)
        ));
        assert_json_path(operation, "$.attributeId ? (@ == \"1\")");

        let conditions =
            ListQueryBuilder::<DatabaseConnection, s3_object::Entity>::json_conditions(
                s3_object::Column::Attributes.into_column_ref(),
                json!({ "attributeId": "a*" }),
                true,
            )
            .unwrap();
        assert_eq!(conditions.len(), 1);

        let operation = conditions[0].clone();
        assert!(matches!(
            operation,
            SimpleExpr::Binary(_, BinOper::Custom("@?"), _)
        ));
        assert_json_path(operation, "$.attributeId ? (@ like_regex \"a.*\")");

        let conditions =
            ListQueryBuilder::<DatabaseConnection, s3_object::Entity>::json_conditions(
                s3_object::Column::Attributes.into_column_ref(),
                json!({ "attributeId": "a*" }),
                false,
            )
            .unwrap();
        assert_eq!(conditions.len(), 1);

        let operation = conditions[0].clone();
        assert!(matches!(
            operation,
            SimpleExpr::Binary(_, BinOper::Custom("@?"), _)
        ));
        assert_json_path(
            operation,
            "$.attributeId ? (@ like_regex \"a.*\" flag \"i\")",
        );
    }

    fn assert_json_path(operation: SimpleExpr, value: &str) {
        if let Binary(_, _, result) = operation {
            assert_eq!(
                Expr::val(value)
                    .cast_as(Alias::new("jsonpath"))
                    .into_simple_expr(),
                *result
            );
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
        offset: u64,
        page_size: u64,
    ) -> Vec<M>
    where
        T: EntityTrait<Model = M>,
        C: ConnectionTrait,
        M: FromQueryResult + Send + Sync,
    {
        builder
            .paginate(offset, page_size)
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
    ) -> Vec<s3_object::Model> {
        filter_all_s3_from(
            client,
            S3ObjectsFilter {
                attributes: filter,
                ..Default::default()
            },
            case_sensitive,
        )
        .await
    }

    async fn filter_all_s3_from(
        client: &Client,
        filter: S3ObjectsFilter,
        case_sensitive: bool,
    ) -> Vec<s3_object::Model> {
        ListQueryBuilder::<_, s3_object::Entity>::new(client.connection_ref())
            .filter_all(filter, case_sensitive)
            .unwrap()
            .all()
            .await
            .unwrap()
    }
}
