//! Filter params for crawl operations.
//!

use crate::database::entities::sea_orm_active_enums::CrawlStatus;
use crate::routes::filter::wildcard::{Wildcard, WildcardEither};
use crate::routes::filter::FilterJoin;
use crate::routes::filter::FilterJoinMerged;
use sea_orm::prelude::DateTimeWithTimeZone;
use serde::{Deserialize, Serialize};
use utoipa::IntoParams;

/// Parameters for listing data for previous and in progress crawls.
#[derive(Serialize, Deserialize, Debug, Default, IntoParams, Clone)]
#[serde(default, rename_all = "camelCase")]
#[into_params(parameter_in = Query)]
pub struct S3CrawlFilter {
    /// List using the bucket. Supports wildcards.
    #[param(nullable = false, required = false, value_type = FilterJoin<Wildcard>)]
    pub(crate) bucket: FilterJoinMerged<Wildcard>,
    /// List using the prefix. Supports wildcards.
    /// Repeated parameters with `[]` are joined with an `or` conditions by default.
    /// Use `[or][]` or `[and][]` to explicitly set the joining logic.
    #[param(nullable = false, required = false, value_type = FilterJoin<Wildcard>)]
    pub(crate) prefix: FilterJoinMerged<Wildcard>,
    /// List using the started date. Supports wildcards.
    /// Repeated parameters with `[]` are joined with an `or` conditions by default.
    /// Use `[or][]` or `[and][]` to explicitly set the joining logic.
    #[param(nullable = false, required = false, value_type = FilterJoin<Wildcard>)]
    pub(crate) started: FilterJoinMerged<WildcardEither<DateTimeWithTimeZone>>,
    /// List using the status.
    /// Repeated parameters with `[]` are joined with an `or` conditions by default.
    /// Use `[or][]` or `[and][]` to explicitly set the joining logic.
    #[param(nullable = false, required = false, value_type = FilterJoin<CrawlStatus>)]
    pub(crate) status: FilterJoinMerged<CrawlStatus>,
}

impl S3CrawlFilter {
    /// Create the crawl params
    pub fn new(
        bucket: FilterJoinMerged<Wildcard>,
        prefix: FilterJoinMerged<Wildcard>,
        started: FilterJoinMerged<WildcardEither<DateTimeWithTimeZone>>,
        status: FilterJoinMerged<CrawlStatus>,
    ) -> Self {
        Self {
            bucket,
            prefix,
            started,
            status,
        }
    }
}
