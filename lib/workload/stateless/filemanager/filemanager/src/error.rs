use std::result;

use sqlx::migrate::MigrateError;
use thiserror::Error;

pub type Result<T> = result::Result<T, Error>;

/// Error types for the filemanager.
#[derive(Error, Debug)]
pub enum Error {
    /// File not found by id.
    #[error("file not found: `{0}`")]
    NotFound(String),
    /// File operation unauthorized
    #[error("unauthorized: `{0}`")]
    Unauthorized(String),
    #[error("SQL error: `{0}`")]
    SQLError(String),
    #[error("SQL migrate error: `{0}`")]
    MigrateError(String),
    #[error("SQS client error: `{0}`")]
    SQSClientError(String),
    #[error("SQS message receive error: `{0}`")]
    SQSReceiveError(String),
    #[error("deserialization error: `{0}`")]
    DeserializeError(String),
    #[error("Db client error: `{0}`")]
    DbClientError(String),
    #[error("S3 object not found: `{0}`")]
    S3ObjectNotFound(String),
    #[error("S3 error: `{0}`")]
    S3Error(String),
    #[error("Config error: `{0}`")]
    ConfigError(String),
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
