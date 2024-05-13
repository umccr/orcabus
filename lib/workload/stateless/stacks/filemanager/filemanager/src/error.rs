//! Errors used by the filemanager crate.
//!

use std::result;

use sqlx::migrate::MigrateError;
use thiserror::Error;

pub type Result<T> = result::Result<T, Error>;

/// Error types for the filemanager.
#[derive(Error, Debug)]
pub enum Error {
    #[error("SQL error: `{0}`")]
    SQLError(String),
    #[error("SQL migrate error: `{0}`")]
    MigrateError(String),
    #[error("SQS error: `{0}`")]
    SQSError(String),
    #[error("deserialization error: `{0}`")]
    DeserializeError(String),
    #[error("Missing environment variable: `{0}`")]
    MissingEnvironmentVariable(String),
    #[error("S3 error: `{0}`")]
    S3Error(String),
    #[error("credential generator error: `{0}`")]
    CredentialGeneratorError(String),
    #[error("S3 inventory error: `{0}`")]
    S3InventoryError(String),
}

impl From<sqlx::Error> for Error {
    fn from(err: sqlx::Error) -> Self {
        Self::SQLError(err.to_string())
    }
}

impl From<MigrateError> for Error {
    fn from(err: MigrateError) -> Self {
        Self::SQLError(err.to_string())
    }
}

impl From<serde_json::Error> for Error {
    fn from(err: serde_json::Error) -> Self {
        Self::DeserializeError(err.to_string())
    }
}
