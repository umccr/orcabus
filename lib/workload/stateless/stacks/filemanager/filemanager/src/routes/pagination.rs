//! Pagination structs and logic for API routes.
//!

use serde::{Deserialize, Deserializer};
use utoipa::{IntoParams, ToSchema};

/// Pagination query parameters for list operations.
#[derive(Debug, Deserialize, IntoParams, ToSchema)]
#[serde(default)]
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
    use axum::body::to_bytes;
    use axum::body::Body;
    use axum::http::Request;
    use parquet::data_type::AsBytes;
    use serde_json::from_slice;
    use sqlx::PgPool;
    use tower::ServiceExt;

    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::entities::object::Model as Object;
    use crate::database::entities::s3_object::Model as S3Object;
    use crate::queries::tests::{initialize_database, initialize_database_reorder};
    use crate::routes::list::ListResponse;
    use crate::routes::{api_router, AppState};

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_objects_api_paginate(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = initialize_database(state.client(), 10).await;

        let app = api_router(state);
        let response = app
            .oneshot(
                Request::builder()
                    .uri("/objects?page=2&page_size=2")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        let result = from_slice::<ListResponse<Object>>(
            to_bytes(response.into_body(), usize::MAX)
                .await
                .unwrap()
                .as_bytes(),
        )
        .unwrap();

        assert_eq!(result.next_page(), Some(3));
        assert_eq!(
            result.results(),
            &entries
                .into_iter()
                .map(|(entry, _)| entry)
                .collect::<Vec<_>>()[4..6]
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_objects_api_zero_page_size(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = initialize_database(state.client(), 10).await;

        let app = api_router(state);
        let response = app
            .oneshot(
                Request::builder()
                    .uri("/s3_objects?page_size=0")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        let result = from_slice::<ListResponse<Object>>(
            to_bytes(response.into_body(), usize::MAX)
                .await
                .unwrap()
                .as_bytes(),
        )
        .unwrap();

        assert_eq!(result.next_page(), None);
        assert_eq!(
            result.results(),
            entries
                .into_iter()
                .map(|(entry, _)| entry)
                .collect::<Vec<_>>()
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_objects_api_paginate(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = initialize_database_reorder(state.client(), 10).await;

        let app = api_router(state);
        let response = app
            .oneshot(
                Request::builder()
                    .uri("/s3_objects?page=1&page_size=2")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        let result = from_slice::<ListResponse<S3Object>>(
            to_bytes(response.into_body(), usize::MAX)
                .await
                .unwrap()
                .as_bytes(),
        )
        .unwrap();

        assert_eq!(result.next_page(), Some(2));
        assert_eq!(
            result.results(),
            &entries
                .into_iter()
                .map(|(_, entry)| entry)
                .collect::<Vec<_>>()[2..4]
        );
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn list_s3_objects_api_zero_page_size(pool: PgPool) {
        let state = AppState::from_pool(pool);
        let entries = initialize_database_reorder(state.client(), 10).await;

        let app = api_router(state);
        let response = app
            .oneshot(
                Request::builder()
                    .uri("/s3_objects?page_size=0")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();

        let result = from_slice::<ListResponse<S3Object>>(
            to_bytes(response.into_body(), usize::MAX)
                .await
                .unwrap()
                .as_bytes(),
        )
        .unwrap();

        assert_eq!(result.next_page(), None);
        assert_eq!(
            result.results(),
            entries
                .into_iter()
                .map(|(_, entry)| entry)
                .collect::<Vec<_>>()
        );
    }
}
