//! Handles loading environment variables as config options for filemanager.
//!

use crate::error::Error::ConfigError;
use crate::error::Result;
use chrono::Duration;
use envy::from_env;
use serde::Deserialize;
use serde_with::serde_as;
use serde_with::DurationSeconds;
use url::Url;

/// Configuration environment variables for filemanager.
#[serde_as]
#[derive(Debug, Clone, Deserialize, Default, Eq, PartialEq)]
pub struct Config {
    pub(crate) database_url: Option<String>,
    pub(crate) pgpassword: Option<String>,
    pub(crate) pghost: Option<String>,
    pub(crate) pgport: Option<u16>,
    pub(crate) pguser: Option<String>,
    #[serde(rename = "filemanager_sqs_url")]
    pub(crate) sqs_url: Option<String>,
    #[serde(default, rename = "filemanager_paired_ingest_mode")]
    pub(crate) paired_ingest_mode: bool,
    #[serde(default, rename = "filemanager_api_links_url")]
    pub(crate) api_links_url: Option<Url>,
    #[serde(rename = "filemanager_api_presign_limit")]
    pub(crate) api_presign_limit: Option<u64>,
    #[serde_as(as = "Option<DurationSeconds<i64>>")]
    #[serde(rename = "filemanager_api_presign_expiry")]
    pub(crate) api_presign_expiry: Option<Duration>,
    #[serde(rename = "filemanager_api_cors_allow_origins")]
    pub(crate) api_cors_allow_origins: Option<Vec<String>>,
}

impl Config {
    /// Load environment variables into a `Config` struct.
    pub fn load() -> Result<Self> {
        let config = from_env::<Self>()?;

        if config.database_url.is_none()
            && config.pgpassword.is_none()
            && config.pghost.is_none()
            && config.pgport.is_none()
            && config.pguser.is_none()
        {
            return Err(ConfigError("no database configuration found".to_string()));
        }

        Ok(config)
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
    pub fn sqs_url(&self) -> Option<&str> {
        self.sqs_url.as_deref()
    }

    /// Get the paired ingest mode.
    pub fn paired_ingest_mode(&self) -> bool {
        self.paired_ingest_mode
    }

    /// Get the presigned size limit.
    pub fn api_links_url(&self) -> Option<&Url> {
        self.api_links_url.as_ref()
    }

    /// Get the presigned size limit.
    pub fn api_presign_limit(&self) -> Option<u64> {
        self.api_presign_limit
    }

    /// Get the presigned expiry time.
    pub fn api_presign_expiry(&self) -> Option<Duration> {
        self.api_presign_expiry
    }

    /// Get the allowed origins
    pub fn api_cors_allow_origins(&self) -> Option<&[String]> {
        self.api_cors_allow_origins.as_deref()
    }

    /// Get the value from an optional, or else try and get a different value, unwrapping into a Result.
    pub fn value_or_else<T>(value: Option<T>, or_else: Option<T>) -> Result<T> {
        value
            .map(Ok)
            .unwrap_or_else(|| Self::value_into_err(or_else))
    }

    /// Convert an optional value to a missing environment variable error.
    pub fn value_into_err<T>(value: Option<T>) -> Result<T> {
        value.ok_or_else(|| ConfigError("missing environment variable".to_string()))
    }
}

#[cfg(test)]
mod tests {
    use envy::from_iter;

    use super::*;

    #[test]
    fn test_environment() {
        let data = vec![
            ("DATABASE_URL", "url"),
            ("PGPASSWORD", "password"),
            ("PGHOST", "host"),
            ("PGPORT", "1234"),
            ("PGUSER", "user"),
            ("FILEMANAGER_SQS_URL", "url"),
            ("FILEMANAGER_PAIRED_INGEST_MODE", "true"),
            ("FILEMANAGER_API_LINKS_URL", "https://localhost:8000"),
            ("FILEMANAGER_API_PRESIGN_LIMIT", "123"),
            ("FILEMANAGER_API_PRESIGN_EXPIRY", "60"),
            (
                "FILEMANAGER_API_CORS_ALLOW_ORIGINS",
                "localhost:8000,127.0.0.1",
            ),
        ]
        .into_iter()
        .map(|(key, value)| (key.to_string(), value.to_string()));

        let config: Config = from_iter(data).unwrap();

        assert_eq!(
            config,
            Config {
                database_url: Some("url".to_string()),
                pgpassword: Some("password".to_string()),
                pghost: Some("host".to_string()),
                pgport: Some(1234),
                pguser: Some("user".to_string()),
                sqs_url: Some("url".to_string()),
                paired_ingest_mode: true,
                api_links_url: Some("https://localhost:8000".parse().unwrap()),
                api_presign_limit: Some(123),
                api_presign_expiry: Some(Duration::seconds(60)),
                api_cors_allow_origins: Some(vec![
                    "localhost:8000".to_string(),
                    "127.0.0.1".to_string()
                ])
            }
        )
    }

    #[test]
    fn test_environment_defaults() {
        let config: Config = from_iter(vec![]).unwrap();

        assert_eq!(config, Default::default());
    }
}
