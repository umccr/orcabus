//! Errors used by the filemanager crate.
//!

use aws_sdk_s3::error::SdkError;
use aws_sdk_s3::operation::list_objects_v2::ListObjectsV2Error;
use sea_orm::{DbErr, RuntimeErr};
use std::num::TryFromIntError;
use std::{io, result};
use thiserror::Error;
use url::ParseError;
use uuid::Uuid;

pub type Result<T> = result::Result<T, Error>;

/// Error types for the filemanager.
#[derive(Error, Debug)]
pub enum Error {
    #[error("database error: `{0}`")]
    DatabaseError(DbErr),
    #[error("SQS error: `{0}`")]
    SQSError(String),
    #[error("serde error: `{0}`")]
    SerdeError(String),
    #[error("loading environment variables: `{0}`")]
    ConfigError(String),
    #[error("credential generator error: `{0}`")]
    CredentialGeneratorError(String),
    #[error("S3 error: `{0}`")]
    S3Error(String),
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
    #[error("error parsing: `{0}`")]
    ParseError(String),
    #[error("missing host header")]
    MissingHostHeader,
    #[error("creating presigned url: `{0}`")]
    PresignedUrlError(String),
    #[error("configuring API: `{0}`")]
    ApiConfigurationError(String),
    #[cfg(feature = "migrate")]
    #[error("SQL migrate error: `{0}`")]
    MigrateError(String),
    #[error("Crawl error: `{0}`")]
    CrawlError(String),
    #[error("Secrets manager error: `{0}`")]
    SecretsManagerError(String),
}

impl From<sqlx::Error> for Error {
    fn from(err: sqlx::Error) -> Self {
        Self::DatabaseError(DbErr::Query(RuntimeErr::SqlxError(err)))
    }
}

impl From<DbErr> for Error {
    fn from(err: DbErr) -> Self {
        Self::DatabaseError(err)
    }
}

impl From<serde_json::Error> for Error {
    fn from(err: serde_json::Error) -> Self {
        Self::SerdeError(err.to_string())
    }
}

impl From<envy::Error> for Error {
    fn from(error: envy::Error) -> Self {
        Self::ConfigError(error.to_string())
    }
}

impl From<ParseError> for Error {
    fn from(error: ParseError) -> Self {
        Self::ParseError(error.to_string())
    }
}

impl From<SdkError<ListObjectsV2Error>> for Error {
    fn from(error: SdkError<ListObjectsV2Error>) -> Self {
        Self::S3Error(error.into_service_error().to_string())
    }
}

impl From<TryFromIntError> for Error {
    fn from(error: TryFromIntError) -> Self {
        Self::ConversionError(error.to_string())
    }
}
