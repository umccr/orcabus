//! Pagination structs and logic for API routes.
//!

use std::num::NonZeroU64;
use std::result;

use serde::{Deserialize, Deserializer, Serialize};
use url::Url;
use utoipa::{IntoParams, ToSchema};

use crate::error::Error::OverflowError;
use crate::error::{Error, Result};

/// The response type for list operations.
#[derive(Debug, Clone, Deserialize, Serialize, ToSchema, Eq, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ListResponse<M> {
    /// Links to next and previous page.
    pub(crate) links: Links,
    /// The pagination response component.
    pub(crate) pagination: PaginatedResponse,
    /// The results of the list operation.
    pub(crate) results: Vec<M>,
}

/// The paginated links to the next and previous page.
#[derive(Debug, Clone, Deserialize, Serialize, ToSchema, Eq, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct Links {
    /// The previous page link.
    previous: Option<Url>,
    /// The next page link.
    next: Option<Url>,
}

impl Links {
    /// Create a new links component.
    pub fn new(previous: Option<Url>, next: Option<Url>) -> Self {
        Self { next, previous }
    }
}

impl<M> ListResponse<M> {
    /// Create a new list response.
    pub fn new(links: Links, pagination: PaginatedResponse, results: Vec<M>) -> Self {
        Self {
            links,
            pagination,
            results,
        }
    }

    /// Create a list response from the results and next page token. Uses the page link
    /// to create links if available.
    pub fn from_next_page(
        pagination: Pagination,
        results: Vec<M>,
        next_page: Option<NonZeroU64>,
        page_link: Url,
        count: u64,
    ) -> Result<Self> {
        let create_link = |page_link: &Url, pagination: Pagination| {
            let query_params = page_link
                .query_pairs()
                .filter(|(key, _)| key != "page")
                .collect::<Vec<_>>();

            let mut page_link = page_link.clone();
            page_link.set_query(None);

            page_link.query_pairs_mut().extend_pairs(query_params);
            page_link
                .query_pairs_mut()
                .append_pair("page", &pagination.page.to_string());

            Ok::<_, Error>(Some(page_link))
        };

        let next = if let Some(next_page) = next_page {
            let qs = Pagination::new(next_page, pagination.rows_per_page());
            create_link(&page_link, qs)?
        } else {
            None
        };

        let previous = if pagination.page().get() == 1 {
            None
        } else {
            let qs = Pagination::from_u64(
                pagination
                    .page()
                    .get()
                    .checked_sub(1)
                    .ok_or_else(|| OverflowError)?,
                pagination.rows_per_page(),
            )?;
            create_link(&page_link, qs)?
        };

        Ok(Self::new(
            Links::new(previous, next),
            PaginatedResponse::new(count, pagination),
            results,
        ))
    }

    /// Get the links.
    pub fn links(&self) -> &Links {
        &self.links
    }

    /// Get the results.
    pub fn results(&self) -> &[M] {
        &self.results
    }

    /// Get the pagination.
    pub fn pagination(&self) -> &PaginatedResponse {
        &self.pagination
    }
}

/// Pagination response component.
#[derive(Debug, Clone, Default, Serialize, Deserialize, ToSchema, Eq, PartialEq)]
#[serde(default, rename_all = "camelCase")]
pub struct PaginatedResponse {
    /// The total number of results in this paginated response.
    #[schema(default = 0)]
    pub(crate) count: u64,
    #[serde(flatten)]
    pub(crate) pagination: Pagination,
}

impl PaginatedResponse {
    /// Create a new paginated response.
    pub fn new(count: u64, pagination: Pagination) -> Self {
        Self { count, pagination }
    }
}

/// Pagination query parameters for list operations.
#[derive(Debug, Clone, Serialize, Deserialize, IntoParams, ToSchema, Eq, PartialEq)]
#[serde(default, rename_all = "camelCase")]
#[into_params(parameter_in = Query)]
pub struct Pagination {
    /// The one-indexed page to fetch from the list of objects.
    /// Increments by 1 starting from 1.
    /// Defaults to the beginning of the collection.
    #[param(required = false, default = 1, minimum = 1, value_type = u64)]
    #[schema(required = false, default = 1, minimum = 1, value_type = u64)]
    page: NonZeroU64,
    /// The number of rows per page, i.e. the page size.
    /// If this is zero then the default is used.
    #[param(required = false, default = 1000)]
    #[serde(deserialize_with = "deserialize_zero_page_as_default")]
    rows_per_page: u64,
}

impl Pagination {
    /// Create a new pagination struct.
    pub fn new(page: NonZeroU64, rows_per_page: u64) -> Self {
        Self {
            page,
            rows_per_page,
        }
    }

    /// Create a new pagination struct.
    pub fn from_u64(page: u64, rows_per_page: u64) -> Result<Self> {
        Ok(Self::new(
            NonZeroU64::new(page).ok_or_else(|| OverflowError)?,
            rows_per_page,
        ))
    }

    /// Get the page.
    pub fn page(&self) -> NonZeroU64 {
        self.page
    }

    /// Get the zero-indexed offset.
    pub fn offset(&self) -> Result<u64> {
        self.page.get().checked_sub(1).ok_or_else(|| OverflowError)
    }

    /// Get the page size.
    pub fn rows_per_page(&self) -> u64 {
        self.rows_per_page
    }
}

/// The default page size.
const DEFAULT_ROWS_PER_PAGE: u64 = 1000;

/// Deserializer to convert a 0 value to the default pagination size.
fn deserialize_zero_page_as_default<'de, D>(deserializer: D) -> result::Result<u64, D::Error>
where
    D: Deserializer<'de>,
{
    let value: u64 = Deserialize::deserialize(deserializer)?;
    if value == 0 {
        Ok(DEFAULT_ROWS_PER_PAGE)
    } else {
        Ok(value)
    }
}

impl Default for Pagination {
    fn default() -> Self {
        Self {
            page: NonZeroU64::new(1).expect("valid non-zero usize"),
            rows_per_page: DEFAULT_ROWS_PER_PAGE,
        }
    }
}

#[cfg(test)]
mod tests {
    use aws_lambda_events::http::StatusCode;
    use axum::body::Body;
    use axum::http::Method;
    use sqlx::PgPool;

    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::entities::s3_object::Model as S3Object;
    use crate::queries::EntriesBuilder;
    use crate::routes::error::ErrorResponse;
    use crate::routes::list::tests::{response_from, response_from_get};
    use crate::routes::AppState;

    use super::*;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_api_paginate(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap()
            .s3_objects;

        let result: ListResponse<S3Object> =
            response_from_get(state.clone(), "/s3?currentState=false&page=2&rowsPerPage=2").await;
        assert_eq!(
            result.links(),
            &Links::new(
                Some(
                    "http://example.com/s3?currentState=false&rowsPerPage=2&page=1"
                        .parse()
                        .unwrap()
                ),
                Some(
                    "http://example.com/s3?currentState=false&rowsPerPage=2&page=3"
                        .parse()
                        .unwrap()
                )
            )
        );
        assert_eq!(result.pagination().count, 10);
        assert_eq!(result.results(), &entries[2..4]);

        let result: ListResponse<S3Object> =
            response_from_get(state.clone(), "/s3?currentState=false&rowsPerPage=2&page=1").await;
        assert_eq!(
            result.links(),
            &Links::new(
                None,
                Some(
                    "http://example.com/s3?currentState=false&rowsPerPage=2&page=2"
                        .parse()
                        .unwrap()
                )
            )
        );
        assert_eq!(result.pagination().count, 10);
        assert_eq!(result.results(), &entries[0..2]);

        let result: ListResponse<S3Object> =
            response_from_get(state.clone(), "/s3?currentState=false&page=5&rowsPerPage=2").await;
        assert_eq!(
            result.links(),
            &Links::new(
                Some(
                    "http://example.com/s3?currentState=false&rowsPerPage=2&page=4"
                        .parse()
                        .unwrap()
                ),
                None
            )
        );
        assert_eq!(result.pagination().count, 10);
        assert_eq!(result.results(), &entries[8..10]);

        let (status_code, _) = response_from::<ErrorResponse>(
            state,
            "/s3?currentState=false&page=0&rowsPerPage=2",
            Method::GET,
            Body::empty(),
        )
        .await;
        assert_eq!(status_code, StatusCode::BAD_REQUEST);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_api_paginate_existing_no_page_size(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .with_n(1001)
            .build(state.database_client())
            .await
            .unwrap()
            .s3_objects;

        let result: ListResponse<S3Object> =
            response_from_get(state.clone(), "/s3?currentState=false&page=1").await;
        assert_eq!(
            result.links(),
            &Links::new(
                None,
                Some(
                    "http://example.com/s3?currentState=false&page=2"
                        .parse()
                        .unwrap()
                )
            )
        );
        assert_eq!(result.pagination().count, 1001);
        assert_eq!(result.results(), &entries[0..1000]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_api_paginate_existing_qs(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap()
            .s3_objects;

        let result: ListResponse<S3Object> = response_from_get(
            state.clone(),
            "/s3?currentState=false&some_parameter=123&page=2&rowsPerPage=2",
        )
        .await;
        assert_eq!(
            result.links(),
            &Links::new(
                Some(
                    "http://example.com/s3?currentState=false&some_parameter=123&rowsPerPage=2&page=1"
                        .parse()
                        .unwrap()
                ),
                Some(
                    "http://example.com/s3?currentState=false&some_parameter=123&rowsPerPage=2&page=3"
                        .parse()
                        .unwrap()
                )
            )
        );
        assert_eq!(result.pagination().count, 10);
        assert_eq!(result.results(), &entries[2..4]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_api_paginate_large(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap()
            .s3_objects;

        let result: ListResponse<S3Object> = response_from_get(
            state.clone(),
            "/s3?currentState=false&page=1&rowsPerPage=20",
        )
        .await;
        assert_eq!(result.links(), &Links::new(None, None));
        assert_eq!(result.pagination().count, 10);
        assert_eq!(result.results(), entries);

        let result: ListResponse<S3Object> =
            response_from_get(state, "/s3?currentState=false&rowsPerPage=1&page=21").await;
        assert_eq!(
            result.links(),
            &Links::new(
                Some(
                    "http://example.com/s3?currentState=false&rowsPerPage=1&page=20"
                        .parse()
                        .unwrap()
                ),
                None,
            )
        );
        assert_eq!(result.pagination().count, 10);
        assert!(result.results().is_empty());
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_api_zero_page_size(pool: PgPool) {
        let state = AppState::from_pool(pool).await.unwrap();

        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.database_client())
            .await
            .unwrap()
            .s3_objects;

        let result: ListResponse<S3Object> =
            response_from_get(state, "/s3?currentState=false&rowsPerPage=0").await;
        assert_eq!(result.links(), &Links::new(None, None));
        assert_eq!(result.pagination().count, 10);
        assert_eq!(result.results(), entries);
    }
}
