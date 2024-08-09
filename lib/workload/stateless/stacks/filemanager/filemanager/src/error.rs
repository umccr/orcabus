//! Errors used by the filemanager crate.
//!

use sea_orm::{sqlx_error_to_query_err, DbErr};
use std::{io, result};

use sqlx::migrate::MigrateError;
use thiserror::Error;
use uuid::Uuid;

pub type Result<T> = result::Result<T, Error>;

/// Error types for the filemanager.
#[derive(Error, Debug)]
pub enum Error {
    #[error("database error: `{0}`")]
    DatabaseError(DbErr),
    #[error("SQL migrate error: `{0}`")]
    MigrateError(String),
    #[error("SQS error: `{0}`")]
    SQSError(String),
    #[error("deserialization error: `{0}`")]
    DeserializeError(String),
    #[error("loading environment variables: `{0}`")]
    ConfigError(String),
    #[error("credential generator error: `{0}`")]
    CredentialGeneratorError(String),
    #[error("S3 inventory error: `{0}`")]
    S3InventoryError(String),
    #[error("{0}")]
    IoError(#[from] io::Error),
    #[error("numerical operation overflowed")]
    OverflowError,
    #[error("numerical conversion failed: `{0}`")]
    ConversionError(String),
    #[error("query error: `{0}`")]
    QueryError(String),
    #[error("invalid input: `{0}`")]
    InvalidQuery(String),
    #[error("expected record for id: `{0}`")]
    ExpectedSomeValue(Uuid),
}

impl From<sqlx::Error> for Error {
    fn from(err: sqlx::Error) -> Self {
        Self::DatabaseError(sqlx_error_to_query_err(err))
    }
}

impl From<DbErr> for Error {
    fn from(err: DbErr) -> Self {
        Self::DatabaseError(err)
    }
}

impl From<MigrateError> for Error {
    fn from(err: MigrateError) -> Self {
        Self::DatabaseError(DbErr::Migration(err.to_string()))
    }
}

impl From<serde_json::Error> for Error {
    fn from(err: serde_json::Error) -> Self {
        Self::DeserializeError(err.to_string())
    }
}

impl From<envy::Error> for Error {
    fn from(error: envy::Error) -> Self {
        Self::ConfigError(error.to_string())
    }
}
