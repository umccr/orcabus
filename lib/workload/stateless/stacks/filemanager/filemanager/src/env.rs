//! Handles loading environment variables as config options for filemanager.
//!

use crate::error::Error::LoadingEnvironment;
use crate::error::Result;
use envy::from_env;
use serde::de::Error;
use serde::{Deserialize, Deserializer};
use std::result;

/// Configuration environment variables for filemanager.
#[derive(Debug, Deserialize, Default)]
pub struct Config {
    pub(crate) database_url: Option<String>,
    pub(crate) pgpassword: Option<String>,
    pub(crate) pghost: Option<String>,
    pub(crate) pgport: Option<u16>,
    pub(crate) pguser: Option<String>,
    pub(crate) sqs_queue_url: Option<String>,
    #[serde(deserialize_with = "deserialize_bool_with_num")]
    pub(crate) paired_ingest_mode: bool,
}

fn deserialize_bool_with_num<'de, D>(deserializer: D) -> result::Result<bool, D::Error>
where
    D: Deserializer<'de>,
{
    let value: Option<String> = Deserialize::deserialize(deserializer)?;

    Ok(value
        .map(|value| {
            if value == "1" {
                Ok(true)
            } else if value == "0" {
                Ok(false)
            } else {
                value.parse::<bool>()
            }
        })
        .transpose()
        .map_err(Error::custom)?
        .unwrap_or_default())
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
        self.sqs_queue_url.as_deref()
    }

    /// Get the paired ingest mode.
    pub fn paired_ingest_mode(&self) -> bool {
        self.paired_ingest_mode
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
