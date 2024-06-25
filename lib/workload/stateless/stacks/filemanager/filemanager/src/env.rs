//! Handles loading environment variables as config options for filemanager.
//!

use crate::error::Error::LoadingEnvironment;
use crate::error::Result;
use envy::from_env;
use serde::Deserialize;

/// Configuration environment variables for filemanager.
#[derive(Debug, Deserialize, Default)]
pub struct Config {
    pub(crate) database_url: Option<String>,
    pub(crate) pgpassword: Option<String>,
    pub(crate) pghost: Option<String>,
    pub(crate) pgport: Option<u16>,
    pub(crate) pguser: Option<String>,
    #[serde(rename = "filemanager_sqs_url")]
    pub(crate) sqs_url: Option<String>,
    #[serde(default)]
    pub(crate) paired_ingest_mode: bool,
    #[serde(rename = "filemanager_api_server_addr")]
    pub(crate) api_server_addr: Option<String>,
}

impl Config {
    /// Load environment variables into a `Config` struct.
    pub fn load() -> Result<Self> {
        Ok(from_env::<Self>()?)
    }

    /// Get the database url.
    pub fn database_url(&self) -> Option<&str> {
        self.database_url.as_deref()
    }

    /// Get the pg password.
    pub fn pg_password(&self) -> Option<&str> {
        self.pgpassword.as_deref()
    }

    /// Get the pg host.
    pub fn pg_host(&self) -> Option<&str> {
        self.pghost.as_deref()
    }

    /// Get the pg port.
    pub fn pg_port(&self) -> Option<u16> {
        self.pgport
    }

    /// Get the pg user.
    pub fn pg_user(&self) -> Option<&str> {
        self.pguser.as_deref()
    }

    /// Get the SQS url.
    pub fn sqs_queue_url(&self) -> Option<&str> {
        self.sqs_url.as_deref()
    }

    /// Get the paired ingest mode.
    pub fn paired_ingest_mode(&self) -> bool {
        self.paired_ingest_mode
    }

    /// Get the api server address.
    pub fn api_server_addr(&self) -> Option<&str> {
        self.api_server_addr.as_deref()
    }

    /// Get the value from an optional, or else try and get a different value, unwrapping into a Result.
    pub fn value_or_else<T>(value: Option<T>, or_else: Option<T>) -> Result<T> {
        value
            .map(Ok)
            .unwrap_or_else(|| Self::value_into_err(or_else))
    }

    /// Convert an optional value to a missing environment variable error.
    pub fn value_into_err<T>(value: Option<T>) -> Result<T> {
        value.ok_or_else(|| LoadingEnvironment("missing environment variable".to_string()))
    }
}
