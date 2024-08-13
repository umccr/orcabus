//! Pagination structs and logic for API routes.
//!

use crate::database::entities::s3_object::Model as S3;
use crate::error::Error::{ConversionError, OverflowError};
use crate::error::{Error, Result};
use serde::{Deserialize, Deserializer, Serialize};
use std::result;
use url::Url;
use utoipa::{IntoParams, ToSchema};

/// The response type for list operations.
#[derive(Debug, Clone, Deserialize, Serialize, ToSchema, Eq, PartialEq)]
#[serde(rename_all = "camelCase")]
#[aliases(ListResponseS3 = ListResponse<S3>)]
pub struct ListResponse<M> {
    /// Links to next and previous page.
    links: Links,
    /// The pagination response component.
    pagination: PaginatedResponse,
    /// The results of the list operation.
    results: Vec<M>,
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
        next_page: Option<u64>,
        page_link: Url,
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

        let previous = if pagination.page() == 0 {
            None
        } else {
            let qs = Pagination::new(
                pagination
                    .page()
                    .checked_sub(1)
                    .ok_or_else(|| OverflowError)?,
                pagination.rows_per_page(),
            );
            create_link(&page_link, qs)?
        };

        let count = u64::try_from(results.len()).map_err(|err| ConversionError(err.to_string()))?;

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
    count: u64,
    #[serde(flatten)]
    pagination: Pagination,
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
    /// The zero-indexed page to fetch from the list of objects.
    /// Increments by 1 starting from 0.
    /// Defaults to the beginning of the collection.
    #[param(nullable, default = 0)]
    page: u64,
    /// The number of rows per page, i.e. the page size.
    /// If this is zero then the default is used.
    #[param(nullable, default = 1000)]
    #[serde(deserialize_with = "deserialize_zero_page_as_default")]
    rows_per_page: u64,
}

impl Pagination {
    /// Create a new pagination struct.
    pub fn new(page: u64, rows_per_page: u64) -> Self {
        Self {
            page,
            rows_per_page,
        }
    }

    /// Get the page.
    pub fn page(&self) -> u64 {
        self.page
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
            page: 0,
            rows_per_page: DEFAULT_ROWS_PER_PAGE,
        }
    }
}

#[cfg(test)]
mod tests {
    use sqlx::PgPool;

    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::entities::s3_object::Model as S3Object;
    use crate::queries::EntriesBuilder;
    use crate::routes::list::tests::response_from_get;
    use crate::routes::AppState;

    use super::*;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_api_paginate(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.client())
            .await
            .s3_objects;

        let result: ListResponse<S3Object> =
            response_from_get(state.clone(), "/s3?page=1&rowsPerPage=2").await;
        assert_eq!(
            result.links(),
            &Links::new(
                Some(
                    "https://example.com/s3?rowsPerPage=2&page=0"
                        .parse()
                        .unwrap()
                ),
                Some(
                    "https://example.com/s3?rowsPerPage=2&page=2"
                        .parse()
                        .unwrap()
                )
            )
        );
        assert_eq!(result.pagination().count, 2);
        assert_eq!(result.results(), &entries[2..4]);

        let result: ListResponse<S3Object> =
            response_from_get(state.clone(), "/s3?rowsPerPage=2&page=0").await;
        assert_eq!(
            result.links(),
            &Links::new(
                None,
                Some(
                    "https://example.com/s3?rowsPerPage=2&page=1"
                        .parse()
                        .unwrap()
                )
            )
        );
        assert_eq!(result.pagination().count, 2);
        assert_eq!(result.results(), &entries[0..2]);

        let result: ListResponse<S3Object> =
            response_from_get(state, "/s3?page=4&rowsPerPage=2").await;
        assert_eq!(
            result.links(),
            &Links::new(
                Some(
                    "https://example.com/s3?rowsPerPage=2&page=3"
                        .parse()
                        .unwrap()
                ),
                None
            )
        );
        assert_eq!(result.pagination().count, 2);
        assert_eq!(result.results(), &entries[8..10]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_api_paginate_existing_no_page_size(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .with_n(1001)
            .build(state.client())
            .await
            .s3_objects;

        let result: ListResponse<S3Object> = response_from_get(state.clone(), "/s3?page=0").await;
        assert_eq!(
            result.links(),
            &Links::new(None, Some("https://example.com/s3?page=1".parse().unwrap()))
        );
        assert_eq!(result.pagination().count, 1000);
        assert_eq!(result.results(), &entries[0..1000]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_api_paginate_existing_qs(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.client())
            .await
            .s3_objects;

        let result: ListResponse<S3Object> =
            response_from_get(state.clone(), "/s3?some_parameter=123&page=1&rowsPerPage=2").await;
        assert_eq!(
            result.links(),
            &Links::new(
                Some(
                    "https://example.com/s3?some_parameter=123&rowsPerPage=2&page=0"
                        .parse()
                        .unwrap()
                ),
                Some(
                    "https://example.com/s3?some_parameter=123&rowsPerPage=2&page=2"
                        .parse()
                        .unwrap()
                )
            )
        );
        assert_eq!(result.pagination().count, 2);
        assert_eq!(result.results(), &entries[2..4]);
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_api_paginate_large(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.client())
            .await
            .s3_objects;

        let result: ListResponse<S3Object> =
            response_from_get(state.clone(), "/s3?page=0&rowsPerPage=20").await;
        assert_eq!(result.links(), &Links::new(None, None));
        assert_eq!(result.pagination().count, 10);
        assert_eq!(result.results(), entries);

        let result: ListResponse<S3Object> =
            response_from_get(state, "/s3?rowsPerPage=1&page=20").await;
        assert_eq!(
            result.links(),
            &Links::new(
                Some(
                    "https://example.com/s3?rowsPerPage=1&page=19"
                        .parse()
                        .unwrap()
                ),
                None,
            )
        );
        assert_eq!(result.pagination().count, 0);
        assert!(result.results().is_empty());
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_api_zero_page_size(pool: PgPool) {
        let state = AppState::from_pool(pool);

        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.client())
            .await
            .s3_objects;

        let result: ListResponse<S3Object> = response_from_get(state, "/s3?rowsPerPage=0").await;
        assert_eq!(result.links(), &Links::new(None, None));
        assert_eq!(result.pagination().count, 10);
        assert_eq!(result.results(), entries);
    }
}
