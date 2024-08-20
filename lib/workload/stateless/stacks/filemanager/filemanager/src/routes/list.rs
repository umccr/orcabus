//! Route logic for list API calls.
//!

use crate::database::entities::s3_object;
use crate::database::entities::s3_object::Model as S3;
use crate::error::Error::{ConversionError, MissingHostHeader, ParseError};
use crate::error::Result;
use crate::queries::list::ListQueryBuilder;
use crate::routes::error::{ErrorStatusCode, QsQuery, Query};
use crate::routes::filter::S3ObjectsFilter;
use crate::routes::pagination::{ListResponse, Pagination};
use crate::routes::presign::{PresignedParams, PresignedUrlBuilder};
use crate::routes::AppState;
use axum::extract::{Request, State};
use axum::http::header::HOST;
use axum::routing::get;
use axum::{extract, Json, Router};
use axum_extra::extract::WithRejection;
use serde::{Deserialize, Serialize};
use std::marker::PhantomData;
use url::Url;
use utoipa::{IntoParams, ToSchema};

/// The return value for count operations showing the number of records in the database.
#[derive(Debug, Deserialize, Serialize, ToSchema, Eq, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ListCount {
    /// The number of records.
    n_records: u64,
}

impl ListCount {
    /// Create a new list count.
    pub fn new(n_records: u64) -> Self {
        ListCount { n_records }
    }

    /// Get the number of records.
    pub fn n_records(&self) -> u64 {
        self.n_records
    }
}

/// Params for wildcard requests.
#[derive(Debug, Deserialize, Default, IntoParams)]
#[serde(default, rename_all = "camelCase")]
#[into_params(parameter_in = Query)]
pub struct WildcardParams {
    /// The case sensitivity when using filter operations with a wildcard.
    /// Setting this true means that an SQL `like` statement is used, and false
    /// means `ilike` is used.
    #[serde(default = "default_case_sensitivity")]
    #[param(nullable, default = true)]
    pub(crate) case_sensitive: bool,
}

impl WildcardParams {
    /// Create new wildcard params.
    pub fn new(case_sensitive: bool) -> Self {
        Self { case_sensitive }
    }

    /// Get the case sensitivity.
    pub fn case_sensitive(&self) -> bool {
        self.case_sensitive
    }
}

/// The default case sensitivity for s3 object filter queries.
pub fn default_case_sensitivity() -> bool {
    true
}

/// Params for a list s3 objects request.
#[derive(Debug, Deserialize, Default, IntoParams)]
#[serde(default, rename_all = "camelCase")]
#[into_params(parameter_in = Query)]
pub struct ListS3Params {
    /// Fetch the current state of objects in storage.
    /// This ensures that only `Created` events which represent current
    /// objects in storage are returned, and any historical `Deleted`
    /// or `Created`events are omitted.
    ///
    /// For example, consider that there are three events for a given bucket, key and version_id
    /// in the following order: `Created` -> `Deleted` -> `Created`. Then setting
    /// `?current_state=true` would return only the last `Created` event.
    #[param(nullable, default = false)]
    current_state: bool,
}

impl ListS3Params {
    /// Create the current state struct.
    pub fn new(current_state: bool) -> Self {
        Self { current_state }
    }

    /// Get the current state.
    pub fn current_state(&self) -> bool {
        self.current_state
    }
}

/// List all s3_objects according to the parameters.
#[utoipa::path(
    get,
    path = "/s3",
    responses(
        (status = OK, description = "The collection of s3_objects", body = ListResponseS3),
        ErrorStatusCode,
    ),
    params(Pagination, WildcardParams, ListS3Params, S3ObjectsFilter),
    context_path = "/api/v1",
    tag = "list",
)]
pub async fn list_s3(
    state: State<AppState>,
    WithRejection(extract::Query(pagination), _): Query<Pagination>,
    WithRejection(extract::Query(wildcard), _): Query<WildcardParams>,
    WithRejection(extract::Query(list), _): Query<ListS3Params>,
    WithRejection(serde_qs::axum::QsQuery(filter_all), _): QsQuery<S3ObjectsFilter>,
    request: Request,
) -> Result<Json<ListResponse<S3>>> {
    let mut response =
        ListQueryBuilder::<_, s3_object::Entity>::new(state.database_client.connection_ref())
            .filter_all(filter_all, wildcard.case_sensitive());

    if list.current_state {
        response = response.current_state();
    }

    let url = if let Some(url) = state.config().api_links_url() {
        url
    } else {
        let mut host = request
            .headers()
            .get(HOST)
            .ok_or_else(|| MissingHostHeader)?
            .to_str()
            .map_err(|err| ParseError(err.to_string()))?
            .to_string();

        // A `HOST` is not a valid URL yet.
        if !host.starts_with("https://") && !host.starts_with("http://") {
            if state.use_tls_links() {
                host = format!("https://{}", host);
            } else {
                host = format!("http://{}", host);
            }
        }

        &host.parse()?
    };

    let url = url.join(&request.uri().to_string())?;

    Ok(Json(
        response.paginate_to_list_response(pagination, url).await?,
    ))
}

/// Count all s3_objects according to the parameters.
#[utoipa::path(
    get,
    path = "/s3/count",
    responses(
        (status = OK, description = "The count of s3 objects", body = ListCount),
        ErrorStatusCode,
    ),
    params(WildcardParams, ListS3Params, S3ObjectsFilter),
    context_path = "/api/v1",
    tag = "list",
)]
pub async fn count_s3(
    state: State<AppState>,
    WithRejection(extract::Query(wildcard), _): Query<WildcardParams>,
    WithRejection(extract::Query(list), _): Query<ListS3Params>,
    WithRejection(serde_qs::axum::QsQuery(filter_all), _): QsQuery<S3ObjectsFilter>,
) -> Result<Json<ListCount>> {
    let mut response =
        ListQueryBuilder::<_, s3_object::Entity>::new(state.database_client.connection_ref())
            .filter_all(filter_all, wildcard.case_sensitive());

    if list.current_state {
        response = response.current_state();
    }

    Ok(Json(response.to_list_count().await?))
}

/// Generate AWS presigned URLs for s3_objects according to the parameters.
/// This route implies `currentState=true` because only existing objects can be presigned.
/// Less presigned URLs may be returned than the amount of objects in the database because some
/// objects may be over the `FILEMANAGER_API_PRESIGN_LIMIT`.
#[utoipa::path(
    get,
    path = "/s3/presign",
    responses(
        (status = OK, description = "The list of presigned urls", body = ListResponseUrl),
        ErrorStatusCode,
    ),
    params(Pagination, WildcardParams, PresignedParams, S3ObjectsFilter),
    context_path = "/api/v1",
    tag = "list",
)]
pub async fn presign_s3(
    state: State<AppState>,
    pagination: Query<Pagination>,
    wildcard: Query<WildcardParams>,
    WithRejection(extract::Query(presigned), _): Query<PresignedParams>,
    filter_all: QsQuery<S3ObjectsFilter>,
    request: Request,
) -> Result<Json<ListResponse<Url>>> {
    let Json(ListResponse {
        links,
        mut pagination,
        results,
    }) = list_s3(
        state.clone(),
        pagination,
        wildcard,
        WithRejection(extract::Query(ListS3Params::new(true)), PhantomData),
        filter_all,
        request,
    )
    .await?;

    let mut urls = Vec::with_capacity(results.len());
    for result in results {
        if let Some(presigned) = PresignedUrlBuilder::presign_from_model(
            &state,
            result,
            presigned.response_content_disposition(),
        )
        .await?
        {
            urls.push(presigned);
        }
    }

    pagination.count = u64::try_from(urls.len()).map_err(|err| ConversionError(err.to_string()))?;

    let response = ListResponse::new(links, pagination, urls);
    Ok(Json(response))
}

/// The router for list objects.
pub fn list_router() -> Router<AppState> {
    Router::new()
        .route("/s3", get(list_s3))
        .route("/s3/count", get(count_s3))
        .route("/s3/presign", get(presign_s3))
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
    use serde::de::DeserializeOwned;
    use serde_json::{from_slice, json};
    use sqlx::PgPool;
    use tower::ServiceExt;

    use super::*;
    use crate::clients::aws::s3;
    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::entities::sea_orm_active_enums::EventType;
    use crate::env::Config;
    use crate::queries::list::tests::filter_event_type;
    use crate::queries::update::tests::change_many;
    use crate::queries::update::tests::{assert_contains, entries_many};
    use crate::queries::EntriesBuilder;
    use crate::routes::api_router;
    use crate::routes::pagination::Links;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_api(pool: PgPool) {
        let state = AppState::from_pool(pool).await;
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .s3_objects;

        let result: ListResponse<S3> = response_from_get(state, "/s3").await;
        assert_eq!(result.links(), &Links::new(None, None));
        assert_eq!(result.results(), entries);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_current_s3_paginate(pool: PgPool) {
        let state = AppState::from_pool(pool).await;
        let entries = EntriesBuilder::default()
            .with_bucket_divisor(4)
            .with_key_divisor(3)
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .s3_objects;

        let result: ListResponse<S3> =
            response_from_get(state, "/s3?currentState=true&rowsPerPage=1&page=1").await;
        assert_eq!(
            result.links(),
            &Links::new(
                None,
                Some(
                    "http://example.com/s3?currentState=true&rowsPerPage=1&page=2"
                        .parse()
                        .unwrap()
                )
            )
        );
        assert_eq!(result.results(), vec![entries[2].clone()]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_current_s3_paginate_https_links(pool: PgPool) {
        let state = AppState::from_pool(pool).await.with_use_tls_links(true);
        let entries = EntriesBuilder::default()
            .with_bucket_divisor(4)
            .with_key_divisor(3)
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .s3_objects;

        let result: ListResponse<S3> =
            response_from_get(state, "/s3?currentState=true&rowsPerPage=1&page=1").await;
        assert_eq!(
            result.links(),
            &Links::new(
                None,
                Some(
                    "https://example.com/s3?currentState=true&rowsPerPage=1&page=2"
                        .parse()
                        .unwrap()
                )
            )
        );
        assert_eq!(result.results(), vec![entries[2].clone()]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_current_s3_paginate_alternate_link(pool: PgPool) {
        let state = AppState::from_pool(pool).await.with_config(Config {
            api_links_url: Some("https://localhost:8000".parse().unwrap()),
            ..Default::default()
        });
        let entries = EntriesBuilder::default()
            .with_bucket_divisor(4)
            .with_key_divisor(3)
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .s3_objects;

        let result: ListResponse<S3> =
            response_from_get(state, "/s3?currentState=true&rowsPerPage=1&page=1").await;
        assert_eq!(
            result.links(),
            &Links::new(
                None,
                Some(
                    "https://localhost:8000/s3?currentState=true&rowsPerPage=1&page=2"
                        .parse()
                        .unwrap()
                )
            )
        );
        assert_eq!(result.results(), vec![entries[2].clone()]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_api_presign(pool: PgPool) {
        let client = mock_client!(
            aws_sdk_s3,
            RuleMode::Sequential,
            &[
                &mock_get_object("0", "0", b""),
                &mock_get_object("2", "2", b"")
            ]
        );

        let state = AppState::from_pool(pool)
            .await
            .with_s3_client(s3::Client::new(client));

        EntriesBuilder::default()
            .with_bucket_divisor(4)
            .with_key_divisor(3)
            .with_shuffle(true)
            .build(state.database_client())
            .await;

        let result: ListResponse<Url> = response_from_get(state, "/s3/presign").await;
        assert_eq!(result.links(), &Links::new(None, None,));
        assert_eq!(2, result.pagination().count);

        let query = result.results()[0].query().unwrap();
        assert!(query.contains("X-Amz-Expires=300"));
        assert!(query.contains("response-content-disposition=inline"));
        assert_eq!(result.results()[0].path(), "/0/0");

        let query = result.results()[1].query().unwrap();
        assert!(query.contains("X-Amz-Expires=300"));
        assert!(query.contains("response-content-disposition=inline"));
        assert_eq!(result.results()[1].path(), "/2/2");
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_api_presign_attachment(pool: PgPool) {
        let client = mock_client!(
            aws_sdk_s3,
            RuleMode::Sequential,
            &[
                &mock_get_object("0", "0", b""),
                &mock_get_object("2", "2", b"")
            ]
        );

        let state = AppState::from_pool(pool)
            .await
            .with_s3_client(s3::Client::new(client));

        EntriesBuilder::default()
            .with_bucket_divisor(4)
            .with_key_divisor(3)
            .with_shuffle(true)
            .build(state.database_client())
            .await;

        let result: ListResponse<Url> =
            response_from_get(state, "/s3/presign?responseContentDisposition=attachment").await;
        assert_eq!(result.links(), &Links::new(None, None,));
        assert_eq!(2, result.pagination().count);

        let query = result.results()[0].query().unwrap();
        assert!(query.contains("X-Amz-Expires=300"));
        assert!(query.contains("response-content-disposition=attachment%3B%20filename%3D%220%22"));
        assert_eq!(result.results()[0].path(), "/0/0");

        let query = result.results()[1].query().unwrap();
        assert!(query.contains("X-Amz-Expires=300"));
        assert!(query.contains("response-content-disposition=attachment%3B%20filename%3D%222%22"));
        assert_eq!(result.results()[1].path(), "/2/2");
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_api_presign_different_count(pool: PgPool) {
        let client = mock_client!(
            aws_sdk_s3,
            RuleMode::Sequential,
            &[&mock_get_object("0", "0", b""),]
        );

        let config = Config {
            api_presign_limit: Some(2),
            ..Default::default()
        };
        let state = AppState::from_pool(pool)
            .await
            .with_config(config)
            .with_s3_client(s3::Client::new(client));

        EntriesBuilder::default()
            .with_bucket_divisor(4)
            .with_key_divisor(3)
            .with_shuffle(true)
            .build(state.database_client())
            .await;

        let result: ListResponse<Url> = response_from_get(state, "/s3/presign").await;
        assert_eq!(result.links(), &Links::new(None, None));
        assert_eq!(1, result.pagination().count);

        let query = result.results()[0].query().unwrap();
        assert!(query.contains("X-Amz-Expires=300"));
        assert!(query.contains("response-content-disposition=inline"));
        assert_eq!(result.results()[0].path(), "/0/0");
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_current_s3_filter(pool: PgPool) {
        let state = AppState::from_pool(pool).await;
        let entries = EntriesBuilder::default()
            .with_n(30)
            .with_bucket_divisor(8)
            .with_key_divisor(5)
            .build(state.database_client())
            .await
            .s3_objects;

        let result: ListResponse<S3> =
            response_from_get(state, "/s3?currentState=true&size=4&rowsPerPage=1&page=1").await;
        assert_eq!(result.links(), &Links::new(None, None));
        assert_eq!(result.results(), vec![entries[24].clone()]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_filter_event_type(pool: PgPool) {
        let state = AppState::from_pool(pool).await;
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .s3_objects;

        let result: ListResponse<S3> = response_from_get(state, "/s3?eventType=Deleted").await;
        assert_eq!(result.results().len(), 5);
        assert_eq!(
            result.results(),
            filter_event_type(entries, EventType::Deleted)
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_multiple_filters(pool: PgPool) {
        let state = AppState::from_pool(pool).await;
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .s3_objects;

        let result: ListResponse<S3> = response_from_get(state, "/s3?bucket=1&key=2").await;
        assert_eq!(result.results(), vec![entries[2].clone()]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_filter_attributes(pool: PgPool) {
        let state = AppState::from_pool(pool).await;
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .s3_objects;

        let result: ListResponse<S3> =
            response_from_get(state.clone(), "/s3?attributes[attributeId]=1").await;
        assert_eq!(result.results(), vec![entries[1].clone()]);

        let result: ListResponse<S3> =
            response_from_get(state.clone(), "/s3?attributes[nestedId][attributeId]=4").await;
        assert_eq!(result.results(), vec![entries[4].clone()]);

        let result: ListResponse<S3> =
            response_from_get(state.clone(), "/s3?attributes[nonExistentId]=1").await;
        assert!(result.results().is_empty());

        let result: ListResponse<S3> =
            response_from_get(state.clone(), "/s3?attributes[attributeId]=1&key=2").await;
        assert!(result.results().is_empty());

        let result: ListResponse<S3> =
            response_from_get(state, "/s3?attributes[attributeId]=1&key=1").await;
        assert_eq!(result.results(), vec![entries[1].clone()]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_filter_attributes_wildcard(pool: PgPool) {
        let state = AppState::from_pool(pool).await;
        let mut entries = EntriesBuilder::default()
            .build(state.database_client())
            .await;

        change_many(
            state.database_client(),
            &entries,
            &[0, 1],
            Some(json!({"attributeId": "attributeId"})),
        )
        .await;

        entries_many(&mut entries, &[0, 1], json!({"attributeId": "attributeId"}));

        let s3_objects: ListResponse<S3> =
            response_from_get(state.clone(), "/s3?attributes[attributeId]=%a%").await;
        assert_contains(s3_objects.results(), &entries, 0..2);

        let s3_objects: ListResponse<S3> =
            response_from_get(state.clone(), "/s3?attributes[attributeId]=%A%").await;
        assert!(s3_objects.results().is_empty());

        let s3_objects: ListResponse<S3> = response_from_get(
            state.clone(),
            "/s3?attributes[attributeId]=%A%&caseSensitive=false",
        )
        .await;
        assert_contains(s3_objects.results(), &entries, 0..2);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn count_s3_api(pool: PgPool) {
        let state = AppState::from_pool(pool).await;
        EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await;

        let result: ListCount = response_from_get(state, "/s3/count").await;
        assert_eq!(result.n_records, 10);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn count_s3_api_filter(pool: PgPool) {
        let state = AppState::from_pool(pool).await;
        EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await;

        let result: ListCount = response_from_get(state, "/s3/count?bucket=0").await;
        assert_eq!(result.n_records, 2);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn count_s3_api_current_state(pool: PgPool) {
        let state = AppState::from_pool(pool).await;
        EntriesBuilder::default()
            .with_bucket_divisor(4)
            .with_key_divisor(3)
            .with_shuffle(true)
            .build(state.database_client())
            .await;

        let result: ListCount = response_from_get(state, "/s3/count?currentState=true").await;
        assert_eq!(result.n_records, 2);
    }

    pub(crate) fn mock_get_object(
        key: &'static str,
        bucket: &'static str,
        output: &'static [u8],
    ) -> Rule {
        mock!(aws_sdk_s3::Client::get_object)
            .match_requests(|req| req.bucket() == Some(bucket) && req.key() == Some(key))
            .then_output(move || {
                GetObjectOutput::builder()
                    .body(ByteStream::from_static(output))
                    .build()
            })
    }

    pub(crate) async fn response_from<T: DeserializeOwned>(
        state: AppState,
        uri: &str,
        method: Method,
        body: Body,
    ) -> (StatusCode, T) {
        let app = api_router(state);
        let response = app
            .oneshot(
                Request::builder()
                    .method(method)
                    .uri(uri)
                    .header(HOST, "example.com")
                    .header(CONTENT_TYPE, "application/json")
                    .body(body)
                    .unwrap(),
            )
            .await
            .unwrap();
        let status = response.status();

        let bytes = to_bytes(response.into_body(), usize::MAX)
            .await
            .unwrap()
            .to_vec();

        (status, from_slice::<T>(bytes.as_slice()).unwrap())
    }

    pub(crate) async fn response_from_get<T: DeserializeOwned>(state: AppState, uri: &str) -> T {
        response_from(state, uri, Method::GET, Body::empty())
            .await
            .1
    }
}
