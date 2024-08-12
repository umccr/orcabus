//! Pagination structs and logic for API routes.
//!

use serde::{Deserialize, Deserializer};
use utoipa::IntoParams;

/// Pagination query parameters for list operations.
#[derive(Debug, Deserialize, IntoParams)]
#[serde(default, rename_all = "camelCase")]
#[into_params(parameter_in = Query)]
pub struct Pagination {
    /// The zero-indexed page to fetch from the list of objects.
    /// Increments by 1 starting from 0.
    /// Defaults to the beginning of the collection.
    #[param(nullable, default = 0)]
    page: u64,
    /// The page to fetch from the list of objects.
    /// If this is zero then the default is used.
    #[param(nullable, default = 1000)]
    #[serde(deserialize_with = "deserialize_zero_page_as_default")]
    page_size: u64,
}

impl Pagination {
    /// Create a new pagination struct.
    pub fn new(page: u64, page_size: u64) -> Self {
        Self { page, page_size }
    }

    /// Get the page.
    pub fn page(&self) -> u64 {
        self.page
    }

    /// Get the page size.
    pub fn page_size(&self) -> u64 {
        self.page_size
    }
}

/// The default page size.
const DEFAULT_PAGE_SIZE: u64 = 1000;

/// Deserializer to convert a 0 value to the default pagination size.
fn deserialize_zero_page_as_default<'de, D>(deserializer: D) -> Result<u64, D::Error>
where
    D: Deserializer<'de>,
{
    let value: u64 = Deserialize::deserialize(deserializer)?;
    if value == 0 {
        Ok(DEFAULT_PAGE_SIZE)
    } else {
        Ok(value)
    }
}

impl Default for Pagination {
    fn default() -> Self {
        Self {
            page: 0,
            page_size: DEFAULT_PAGE_SIZE,
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
    use crate::routes::list::ListResponse;
    use crate::routes::AppState;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_api_paginate(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = EntriesBuilder::default()
            .with_shuffle(true)
            .build(state.client())
            .await
            .s3_objects;

        let result: ListResponse<S3Object> =
            response_from_get(state, "/s3?page=1&pageSize=2").await;
        assert_eq!(result.next_page(), Some(2));
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
            response_from_get(state.clone(), "/s3?page=0&pageSize=20").await;
        assert!(result.next_page().is_none());
        assert_eq!(result.results(), entries);

        let result: ListResponse<S3Object> =
            response_from_get(state, "/s3?page=20&pageSize=1").await;
        assert!(result.next_page().is_none());
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

        let result: ListResponse<S3Object> = response_from_get(state, "/s3?pageSize=0").await;
        assert_eq!(result.next_page(), None);
        assert_eq!(result.results(), entries);
    }
}
