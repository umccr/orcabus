//! Adds a route to fetch all records from S3 using list operations and update the database.
//!

use crate::database::entities::s3_crawl::Model as Crawl;
use crate::database::entities::sea_orm_active_enums::CrawlStatus;
use crate::error::Result;
use crate::routes::error::{ErrorStatusCode, Path, QsQuery, Query};
use crate::routes::filter::crawl::CrawlListParams;
use crate::routes::filter::S3ObjectsFilter;
use crate::routes::header::HeaderParser;
use crate::routes::list::{
    attributes_s3, count_s3, list_s3, presign_s3, ListS3Params, WildcardParams,
};
use crate::routes::pagination::{Links, ListResponse, Pagination};
use crate::routes::presign::{PresignedParams, PresignedUrlBuilder};
use crate::routes::AppState;
use aws_lambda_events::http::header::{CONTENT_ENCODING, CONTENT_TYPE};
use axum::extract::{Request, State};
use axum::response::NoContent;
use axum::routing::{get, post};
use axum::{extract, Json, Router};
use axum_extra::extract::WithRejection;
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
        execution_time: None,
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
    params(Pagination, WildcardParams, CrawlListParams),
    context_path = "/api/v1",
    tag = "crawl",
)]
pub async fn list_crawl(
    state: State<AppState>,
    WithRejection(extract::Query(pagination), _): Query<Pagination>,
    WithRejection(extract::Query(wildcard), _): Query<WildcardParams>,
    WithRejection(extract::Query(list), _): Query<CrawlListParams>,
) -> Result<Json<ListResponse<Crawl>>> {
    Ok(Json(ListResponse {
        links: Links::new(None, None),
        pagination: Default::default(),
        results: vec![],
    }))
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
pub async fn get_crawl_by_id(state: State<AppState>, id: Path<Uuid>) -> Result<Json<Crawl>> {
    Ok(Json(Crawl {
        s3_crawl_id: Default::default(),
        status: CrawlStatus::Completed,
        started: Default::default(),
        bucket: "".to_string(),
        prefix: None,
        execution_time: None,
        n_objects: None,
    }))
}

/// The router for crawl operations.
pub fn crawl_router() -> Router<AppState> {
    Router::new()
        .route("/s3/crawl", post(crawl_s3))
        .route("s3/crawl/sync", post(crawl_sync_s3))
        .route("/s3/crawl/status", get(list_crawl))
        .route("/s3/crawl/status/:id", get(get_crawl_by_id))
}
