//! Adds a route to fetch all records from S3 using list operations and update the database.
//!

use crate::database::entities::s3_crawl;
use crate::database::entities::s3_crawl::Model as Crawl;
use crate::database::entities::sea_orm_active_enums::CrawlStatus;
use crate::database::entities::sea_orm_active_enums::CrawlStatus::InProgress;
use crate::database::Ingest;
use crate::error::Error::{CrawlError, ExpectedSomeValue};
use crate::error::{Error, Result};
use crate::events::aws::collecter::CollecterBuilder;
use crate::events::aws::crawl;
use crate::events::Collect;
use crate::queries::get::GetQueryBuilder;
use crate::queries::list::ListQueryBuilder;
use crate::routes::error::{ErrorStatusCode, Json, Path, QsQuery, Query};
use crate::routes::filter::crawl::S3CrawlFilter;
use crate::routes::filter::wildcard::Wildcard;
use crate::routes::filter::S3ObjectsFilter;
use crate::routes::header::HeaderParser;
use crate::routes::list::{ListCount, ListS3Params, WildcardParams};
use crate::routes::pagination::{ListResponse, Pagination};
use crate::routes::AppState;
use crate::uuid::UuidGenerator;
use axum::extract::{Request, State};
use axum::response::NoContent;
use axum::routing::{get, post};
use axum::{extract, Router};
use axum_extra::extract::WithRejection;
use chrono::{TimeDelta, Utc};
use sea_orm::ActiveValue::Set;
use sea_orm::{ActiveModelTrait, ConnectionTrait, EntityTrait, IntoActiveModel, TransactionTrait};
use serde::{Deserialize, Serialize};
use std::marker::PhantomData;
use utoipa::{IntoParams, ToSchema};
use uuid::Uuid;

/// The maximum time a crawl can run for.
pub const MAX_CRAWL_TIME_MINUTES: i64 = 15;

/// Request for initiating a crawl.
#[derive(Serialize, Deserialize, Debug, Default, IntoParams, ToSchema)]
#[serde(default, rename_all = "camelCase")]
#[into_params(parameter_in = Query)]
pub struct CrawlRequest {
    /// Specify the bucket to crawl.
    #[param(nullable = false, required = true)]
    bucket: String,
    /// Specify the prefix to crawl from. By default, crawls all files in the bucket.
    #[param(nullable = true, required = false)]
    prefix: Option<String>,
}

impl CrawlRequest {
    /// Create crawl params.
    pub fn new(bucket: String, prefix: Option<String>) -> Self {
        Self { bucket, prefix }
    }

    /// Get the bucket.
    pub fn bucket(&self) -> &str {
        &self.bucket
    }

    /// Get the prefix.
    pub fn prefix(&self) -> Option<&str> {
        self.prefix.as_deref()
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
    request_body = CrawlRequest,
    context_path = "/api/v1",
    tag = "crawl",
)]
pub async fn crawl_s3(
    state: State<AppState>,
    WithRejection(extract::Json(crawl), _): Json<CrawlRequest>,
) -> Result<NoContent> {
    let state_copy = state.clone();

    // The reference to this task is effectively lost to external callers of the API, however
    // it can be retrieved from the state internally.
    let handle = tokio::spawn(async move {
        crawl_sync_s3(state_copy, WithRejection(extract::Json(crawl), PhantomData)).await
    });

    let mut task = state.crawl_task.lock().await;
    *task = Some(handle);

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
    request_body = CrawlRequest,
    context_path = "/api/v1",
    tag = "crawl",
)]
pub async fn crawl_sync_s3(
    state: State<AppState>,
    WithRejection(extract::Json(crawl), _): Json<CrawlRequest>,
) -> Result<extract::Json<Crawl>> {
    let conn = state.database_client().connection_ref();

    let in_progress = ListQueryBuilder::<_, s3_crawl::Entity>::new(conn)
        .filter_all(
            S3CrawlFilter {
                bucket: Wildcard::new(crawl.bucket.to_string()).into(),
                status: InProgress.into(),
                ..Default::default()
            },
            true,
        )?
        .one()
        .await?;

    // If there is a crawl in progress already, then this is an error.
    if let Some(in_progress) = in_progress {
        // Just in case the crawl has been running too long, fail it here.
        let diff = Utc::now().signed_duration_since(in_progress.started);
        if diff < TimeDelta::zero() || diff > TimeDelta::minutes(MAX_CRAWL_TIME_MINUTES) {
            let mut to_update = in_progress.into_active_model();
            to_update.status = Set(CrawlStatus::Failed);
            to_update.update(conn).await?;
        }

        return Err(CrawlError(format!(
            "another crawl on {} is already in progress",
            crawl.bucket
        )));
    }

    // New crawl can be started.
    let uuid = UuidGenerator::generate();
    let mut crawl_execution = s3_crawl::ActiveModel {
        s3_crawl_id: Set(uuid),
        bucket: Set(crawl.bucket.to_string()),
        prefix: Set(crawl.prefix.clone()),
        status: Set(InProgress),
        ..Default::default()
    };
    crawl_execution.clone().insert(conn).await?;

    let now = Utc::now();
    let set_failed = |mut to_update: s3_crawl::ActiveModel| async {
        to_update.status = Set(CrawlStatus::Failed);
        Ok::<_, Error>(to_update.update(conn).await?)
    };

    // Get crawl list object details.
    let crawl = crawl::Crawl::new(state.s3_client().clone())
        .crawl_s3(&crawl.bucket, crawl.prefix)
        .await;
    if let Err(err) = crawl {
        set_failed(crawl_execution).await?;
        return Err(err);
    }

    let crawl = crawl?;
    let n_events = i64::try_from(crawl.0.len())?;

    // Update events.
    let events = CollecterBuilder::default()
        .with_s3_client(state.s3_client().clone())
        .build(crawl, state.config(), state.database_client())
        .await
        .collect()
        .await;
    if let Err(err) = events {
        set_failed(crawl_execution).await?;
        return Err(err);
    }

    let events = events?.into_inner().0;

    // Ingest events.
    if let Err(err) = state.database_client().ingest(events).await {
        set_failed(crawl_execution).await?;
        return Err(err);
    }

    // Update crawl entry.
    crawl_execution.status = Set(CrawlStatus::Completed);
    crawl_execution.execution_time_seconds = Set(Some(i32::try_from(
        now.signed_duration_since(Utc::now()).abs().num_seconds(),
    )?));
    crawl_execution.n_objects = Set(Some(n_events));
    crawl_execution.clone().update(conn).await?;

    let entry = s3_crawl::Entity::find_by_id(uuid)
        .one(conn)
        .await?
        .ok_or_else(|| CrawlError("expected crawl entry".to_string()))?;
    Ok(extract::Json(entry))
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
) -> Result<extract::Json<ListResponse<Crawl>>> {
    let txn = state.database_client().connection_ref().begin().await?;

    let response = ListQueryBuilder::<_, s3_crawl::Entity>::new(&txn)
        .filter_all(filter.clone(), wildcard.case_sensitive())?;

    let url = if let Some(url) = state.config().api_links_url() {
        url
    } else {
        &HeaderParser::parse_host_url(&request, state.use_tls_links())?
    };

    let url = url.join(&HeaderParser::get_uri_path(&request))?;

    let extract::Json(count) = count_crawl_with_connection(
        &txn,
        WithRejection(extract::Query(wildcard), PhantomData),
        WithRejection(serde_qs::axum::QsQuery(filter), PhantomData),
    )
    .await?;
    let response = response
        .paginate_to_list_response(pagination, url, count.n_records())
        .await?;

    txn.commit().await?;

    Ok(extract::Json(response))
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
) -> Result<extract::Json<ListCount>> {
    count_crawl_with_connection(state.database_client().connection_ref(), wildcard, filter).await
}

async fn count_crawl_with_connection<C: ConnectionTrait>(
    connection: &C,
    WithRejection(extract::Query(wildcard), _): Query<WildcardParams>,
    WithRejection(serde_qs::axum::QsQuery(filter), _): QsQuery<S3CrawlFilter>,
) -> Result<extract::Json<ListCount>> {
    let response = ListQueryBuilder::<_, s3_crawl::Entity>::new(connection)
        .filter_all(filter, wildcard.case_sensitive())?;

    Ok(extract::Json(response.to_list_count().await?))
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
) -> Result<extract::Json<Crawl>> {
    let query = GetQueryBuilder::new(state.database_client().connection_ref());

    Ok(extract::Json(
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
        .route("/s3/crawl/status/{id}", get(get_crawl_s3_by_id))
}

#[cfg(test)]
pub(crate) mod tests {
    use crate::database::aws::migration::tests::MIGRATOR;
    use aws_lambda_events::http::Method;
    use axum::body::Body;
    use axum::http::StatusCode;
    use sqlx::PgPool;

    use super::*;
    use crate::clients::aws::s3::Client;
    use crate::clients::aws::{secrets_manager, sqs};
    use crate::database;
    use crate::database::entities::sea_orm_active_enums::CrawlStatus::Completed;
    use crate::events::aws::collecter::tests::{
        expected_get_object_tagging, expected_head_object, expected_put_object_tagging,
        get_tagging_expectation, head_expectation, put_tagging_expectation,
    };
    use crate::events::aws::crawl::tests::list_object_expectations;
    use crate::events::aws::message::default_version_id;
    use crate::queries::list::tests::assert_crawl_entries;
    use crate::queries::EntriesBuilder;
    use crate::routes::list::tests::{response_from, response_from_get};
    use crate::routes::pagination::Links;
    use serde_json::json;
    use std::sync::Arc;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn crawl_s3_api(pool: PgPool) {
        let client = crawl_expectations();

        let state = AppState::new(
            database::Client::from_pool(pool),
            Default::default(),
            Arc::new(client),
            Arc::new(sqs::Client::with_defaults().await),
            Arc::new(secrets_manager::Client::with_defaults().await.unwrap()),
            false,
        );

        EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap();

        let result: Crawl = response_from(
            state.clone(),
            "/s3/crawl/sync",
            Method::POST,
            Body::from(json!({"bucket": "bucket", "prefix": "prefix"}).to_string()),
        )
        .await
        .1;

        assert_eq!(result.status, Completed);
        assert_eq!(result.n_objects, Some(2));

        let (status, _) = crawl(&state).await;

        assert_eq!(status, StatusCode::NO_CONTENT);
        let result = state.into_crawl_result().await.unwrap();

        assert_eq!(result.status, Completed);
        assert_eq!(result.n_objects, Some(2));
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn crawl_s3_status_api(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
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
    async fn count_s3_status_api(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap();

        let result: ListCount = response_from_get(state, "/s3/crawl/status/count").await;
        assert_eq!(result.n_records(), 10);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn get_s3_status_api(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
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

    async fn crawl(state: &AppState) -> (StatusCode, serde_json::Value) {
        response_from(
            state.clone(),
            "/s3/crawl",
            Method::POST,
            Body::from(json!({"bucket": "bucket", "prefix": "prefix"}).to_string()),
        )
        .await
    }

    fn crawl_expectations() -> Client {
        list_object_expectations(&[
            head_expectation(default_version_id().to_string(), expected_head_object()),
            put_tagging_expectation(
                default_version_id().to_string(),
                expected_put_object_tagging(),
            ),
            get_tagging_expectation(
                default_version_id().to_string(),
                expected_get_object_tagging(),
            ),
        ])
    }
}
