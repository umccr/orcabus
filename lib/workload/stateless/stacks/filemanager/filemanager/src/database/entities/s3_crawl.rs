//! `SeaORM` Entity, @generated by sea-orm-codegen 1.1.2
use super::sea_orm_active_enums::CrawlStatus;
use sea_orm::entity::prelude::*;
use serde::{Deserialize, Serialize};
#[derive(
    Clone, Debug, PartialEq, DeriveEntityModel, Eq, Serialize, Deserialize, utoipa::ToSchema,
)]
#[sea_orm(table_name = "s3_crawl")]
#[serde(rename_all = "camelCase")]
#[schema(as = S3Crawl)]
pub struct Model {
    #[sea_orm(primary_key, auto_increment = false)]
    pub s3_crawl_id: Uuid,
    pub status: CrawlStatus,
    pub started: chrono::DateTime<chrono::FixedOffset>,
    #[sea_orm(column_type = "Text", unique)]
    pub bucket: String,
    #[sea_orm(column_type = "Text", nullable)]
    pub prefix: Option<String>,
    pub execution_time: Option<String>,
    pub n_objects: Option<i64>,
}
#[derive(Copy, Clone, Debug, EnumIter, DeriveRelation)]
pub enum Relation {}
impl ActiveModelBehavior for ActiveModel {}
