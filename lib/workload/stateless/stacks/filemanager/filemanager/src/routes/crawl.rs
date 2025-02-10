//! Adds a route to fetch all records from S3 using list operations and update the database.
//!

use crate::database::entities::s3_crawl::Model as Crawl;
use crate::database::entities::sea_orm_active_enums::CrawlStatus;
use crate::database::entities::{s3_crawl, s3_object};
use crate::error::Error::{ExpectedSomeValue, MissingHostHeader};
use crate::error::Result;
use crate::queries::get::GetQueryBuilder;
use crate::queries::list::ListQueryBuilder;
use crate::routes::error::{ErrorStatusCode, Path, QsQuery, Query};
use crate::routes::filter::crawl::S3CrawlFilter;
use crate::routes::filter::S3ObjectsFilter;
use crate::routes::header::HeaderParser;
use crate::routes::list::{
    attributes_s3, count_s3, list_s3, presign_s3, ListCount, ListS3Params, WildcardParams,
};
use crate::routes::pagination::{Links, ListResponse, Pagination};
use crate::routes::presign::{PresignedParams, PresignedUrlBuilder};
use crate::routes::AppState;
use arrow::compute::starts_with;
use aws_lambda_events::http::header::{CONTENT_ENCODING, CONTENT_TYPE, HOST};
use axum::extract::{Request, State};
use axum::response::NoContent;
use axum::routing::{get, post};
use axum::{extract, Json, Router};
use axum_extra::extract::WithRejection;
use sea_orm::{ConnectionTrait, TransactionTrait};
use serde::{Deserialize, Serialize};
use std::marker::PhantomData;
use url::Url;
use utoipa::IntoParams;
use uuid::Uuid;

/// Parameters for initiating a crawl.
#[derive(Serialize, Deserialize, Debug, Default, IntoParams)]
#[serde(default, rename_all = "camelCase")]
#[into_params(parameter_in = Query)]
pub struct CrawlParams {
    /// Specify the bucket to crawl.
    #[param(nullable = false, required = true)]
    bucket: String,
    /// Specify the prefix to crawl from. By default, crawls all files in the bucket.
    #[param(nullable = false, required = false, default = "")]
    prefix: String,
}

impl CrawlParams {
    /// Create crawl params.
    pub fn new(bucket: String, prefix: String) -> Self {
        Self { bucket, prefix }
    }

    /// Get the bucket.
    pub fn bucket(&self) -> &str {
        &self.bucket
    }

    /// Get the prefix.
    pub fn prefix(&self) -> &str {
        &self.prefix
    }
}

/// Crawl S3, updating existing records and adding new ones into the database based on `ListObjects`.
/// Only one crawl can be run at a time for a specific bucket. The crawl is atomic, so if it fails,
/// no new records will be ingested.
///
/// This crawl is asynchronous and will return immediately but continue processing in the background.
/// To query the status of asynchronous crawls, use `/api/v1/s3/crawl/status`. Alternatively use
/// `/api/v1/s3/crawl/sync` for a synchronous variant of this API call.
#[utoipa::path(
    post,
    path = "/s3/crawl",
    responses(
        (
            status = NO_CONTENT,
            description = "The crawl operation was started if there were no existing crawls in progress",
        ),
        ErrorStatusCode,
    ),
    params(CrawlParams),
    context_path = "/api/v1",
    tag = "crawl",
)]
pub async fn crawl_s3(
    state: State<AppState>,
    WithRejection(extract::Query(crawl), _): Query<CrawlParams>,
) -> Result<NoContent> {
    Ok(NoContent)
}

/// Crawl S3, updating existing records and adding new ones into the database based on `ListObjects`.
/// Only one crawl can be run at a time for a specific bucket. The crawl is atomic, so if it fails,
/// no new records will be ingested.
///
/// This crawl is synchronous and will wait until the crawl is complete before returning a response.
/// If the crawl exceeds the timeout of the API, use `/api/v1/s3/crawl` instead.
#[utoipa::path(
    post,
    path = "/s3/crawl/sync",
    responses(
        (status = OK, description = "The result of the crawl", body = Crawl),
        ErrorStatusCode,
    ),
    params(CrawlParams),
    context_path = "/api/v1",
    tag = "crawl",
)]
pub async fn crawl_sync_s3(
    state: State<AppState>,
    WithRejection(extract::Query(crawl), _): Query<CrawlParams>,
) -> Result<Json<Crawl>> {
    Ok(Json(Crawl {
        s3_crawl_id: Default::default(),
        status: CrawlStatus::Completed,
        started: Default::default(),
        bucket: "".to_string(),
        prefix: None,
        execution_time_seconds: None,
        n_objects: None,
    }))
}

/// Get the in-progress or previous crawl executions.
#[utoipa::path(
    get,
    path = "/s3/crawl/status",
    responses(
        (status = OK, description = "The result of the crawl", body = ListResponse<Crawl>),
        ErrorStatusCode,
    ),
    params(Pagination, WildcardParams, S3CrawlFilter),
    context_path = "/api/v1",
    tag = "crawl",
)]
pub async fn list_crawl_s3(
    state: State<AppState>,
    WithRejection(extract::Query(pagination), _): Query<Pagination>,
    WithRejection(extract::Query(wildcard), _): Query<WildcardParams>,
    WithRejection(serde_qs::axum::QsQuery(filter), _): QsQuery<S3CrawlFilter>,
    request: Request,
) -> Result<Json<ListResponse<Crawl>>> {
    let txn = state.database_client().connection_ref().begin().await?;

    let response = ListQueryBuilder::<_, s3_crawl::Entity>::new(&txn)
        .filter_all(filter.clone(), wildcard.case_sensitive())?;

    let url = if let Some(url) = state.config().api_links_url() {
        url
    } else {
        &HeaderParser::parse_host_url(&request, state.use_tls_links())?
    };

    let url = url.join(&request.uri().to_string())?;

    let Json(count) = count_crawl_with_connection(
        &txn,
        WithRejection(extract::Query(wildcard), PhantomData),
        WithRejection(serde_qs::axum::QsQuery(filter), PhantomData),
    )
    .await?;
    let response = response
        .paginate_to_list_response(pagination, url, count.n_records())
        .await?;

    txn.commit().await?;

    Ok(Json(response))
}

/// Count all s3 crawl requests according to the parameters.
#[utoipa::path(
    get,
    path = "/crawl/status/count",
    responses(
        (status = OK, description = "The count of crawl requests", body = ListCount),
        ErrorStatusCode,
    ),
    params(WildcardParams, ListS3Params, S3ObjectsFilter),
    context_path = "/api/v1",
    tag = "list",
)]
pub async fn count_crawl_s3(
    state: State<AppState>,
    wildcard: Query<WildcardParams>,
    filter: QsQuery<S3CrawlFilter>,
) -> Result<Json<ListCount>> {
    count_crawl_with_connection(state.database_client().connection_ref(), wildcard, filter).await
}

async fn count_crawl_with_connection<C: ConnectionTrait>(
    connection: &C,
    WithRejection(extract::Query(wildcard), _): Query<WildcardParams>,
    WithRejection(serde_qs::axum::QsQuery(filter), _): QsQuery<S3CrawlFilter>,
) -> Result<Json<ListCount>> {
    let response = ListQueryBuilder::<_, s3_crawl::Entity>::new(connection)
        .filter_all(filter, wildcard.case_sensitive())?;

    Ok(Json(response.to_list_count().await?))
}

/// Get the crawl execution using the id.
#[utoipa::path(
    get,
    path = "/crawl/status/{id}",
    responses(
        (status = OK, description = "The crawl execution for the given id", body = Crawl),
        ErrorStatusCode,
    ),
    context_path = "/api/v1",
    tag = "crawl",
)]
pub async fn get_crawl_s3_by_id(
    state: State<AppState>,
    WithRejection(extract::Path(id), _): Path<Uuid>,
) -> Result<Json<Crawl>> {
    let query = GetQueryBuilder::new(state.database_client().connection_ref());

    Ok(Json(
        query
            .get_crawl_by_id(id)
            .await?
            .ok_or_else(|| ExpectedSomeValue(id))?,
    ))
}

/// The router for crawl operations.
pub fn crawl_router() -> Router<AppState> {
    Router::new()
        .route("/s3/crawl", post(crawl_s3))
        .route("/s3/crawl/sync", post(crawl_sync_s3))
        .route("/s3/crawl/status", get(list_crawl_s3))
        .route("/s3/crawl/status/count", get(count_crawl_s3))
        .route("/s3/crawl/status/:id", get(get_crawl_s3_by_id))
}

#[cfg(test)]
pub(crate) mod tests {
    use aws_sdk_s3::operation::get_object::GetObjectOutput;
    use aws_sdk_s3::primitives::ByteStream;
    use aws_smithy_mocks_experimental::{mock, mock_client, Rule, RuleMode};
    use axum::body::to_bytes;
    use axum::body::Body;
    use axum::http::header::CONTENT_TYPE;
    use axum::http::{Method, Request, StatusCode};
    use percent_encoding::{percent_encode, NON_ALPHANUMERIC};
    use serde::de::DeserializeOwned;
    use serde_json::{from_slice, json};
    use sqlx::PgPool;
    use std::collections::HashMap;
    use tower::util::ServiceExt;
    use uuid::Uuid;

    use crate::clients::aws::s3;
    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::entities::sea_orm_active_enums::EventType;
    use crate::env::Config;
    use crate::queries::list::tests::assert_crawl_entries;
    use crate::queries::list::tests::filter_event_type;
    use crate::queries::update::tests::{assert_contains, entries_many};
    use crate::queries::update::tests::{change_key, change_many};
    use crate::queries::EntriesBuilder;
    use crate::routes::api_router;
    use crate::routes::list::tests::response_from_get;
    use crate::routes::pagination::Links;
    use crate::routes::presign::tests::assert_presigned_params;

    use super::*;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn crawl_s3_api(pool: PgPool) {
        let state = AppState::from_pool(pool).await;
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap()
            .s3_crawl;

        let result: ListResponse<Crawl> =
            response_from_get(state.clone(), "/s3/crawl/status").await;
        assert_eq!(result.links(), &Links::new(None, None));

        assert_crawl_entries(result.results(), &entries);
        assert_eq!(result.pagination().count, 10);

        let result: ListResponse<Crawl> =
            response_from_get(state, "/s3/crawl/status?bucket=0&prefix=1").await;
        assert_eq!(result.links(), &Links::new(None, None));

        assert_eq!(result.results(), vec![entries[1].clone()]);
        assert_eq!(result.pagination().count, 1);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn count_s3_api(pool: PgPool) {
        let state = AppState::from_pool(pool).await;
        EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap();

        let result: ListCount = response_from_get(state, "/s3/crawl/status/count").await;
        assert_eq!(result.n_records(), 10);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn get_s3_api(pool: PgPool) {
        let state = AppState::from_pool(pool).await;
        let entries = EntriesBuilder::default()
            .build(state.database_client())
            .await
            .unwrap()
            .s3_crawl;

        let first = entries.first().unwrap();
        let result: s3_crawl::Model =
            response_from_get(state, &format!("/s3/crawl/status/{}", first.s3_crawl_id)).await;
        assert_eq!(&result, first);
    }
}
