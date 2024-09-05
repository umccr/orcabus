//! `SeaORM` Entity, @generated by sea-orm-codegen 1.1.0-rc.1
use sea_orm::entity::prelude::*;
use serde::{Deserialize, Serialize};
#[derive(
    Debug,
    Clone,
    PartialEq,
    Eq,
    EnumIter,
    DeriveActiveEnum,
    Serialize,
    Deserialize,
    strum::FromRepr,
    strum::EnumCount,
    utoipa::ToSchema,
)]
#[sea_orm(rs_type = "String", db_type = "Enum", enum_name = "event_type")]
#[repr(u8)]
pub enum EventType {
    #[sea_orm(string_value = "Created")]
    Created,
    #[sea_orm(string_value = "Deleted")]
    Deleted,
    #[sea_orm(string_value = "Other")]
    Other,
}
#[derive(
    Debug,
    Clone,
    PartialEq,
    Eq,
    EnumIter,
    DeriveActiveEnum,
    Serialize,
    Deserialize,
    strum::FromRepr,
    strum::EnumCount,
    utoipa::ToSchema,
)]
#[sea_orm(rs_type = "String", db_type = "Enum", enum_name = "storage_class")]
#[repr(u8)]
pub enum StorageClass {
    #[sea_orm(string_value = "DeepArchive")]
    DeepArchive,
    #[sea_orm(string_value = "Glacier")]
    Glacier,
    #[sea_orm(string_value = "GlacierIr")]
    GlacierIr,
    #[sea_orm(string_value = "IntelligentTiering")]
    IntelligentTiering,
    #[sea_orm(string_value = "OnezoneIa")]
    OnezoneIa,
    #[sea_orm(string_value = "Outposts")]
    Outposts,
    #[sea_orm(string_value = "ReducedRedundancy")]
    ReducedRedundancy,
    #[sea_orm(string_value = "Snow")]
    Snow,
    #[sea_orm(string_value = "Standard")]
    Standard,
    #[sea_orm(string_value = "StandardIa")]
    StandardIa,
}
