//! Handles loading environment variables as config options for filemanager.
//!

use std::result;
use envy::from_env;
use serde::{Deserialize, Deserializer};
use serde::de::Error;
use crate::error::Result;

/// Configuration environment variables for filemanager.
#[derive(Debug, Deserialize)]
pub struct Config {
    database_url: Option<String>,
    pgpassword: Option<String>,
    pghost: Option<String>,
    pgport: Option<String>,
    pguser: Option<String>,
    sqs_queue_url: Option<String>,
    #[serde(deserialize_with = "deserialize_bool_with_num")]
    paired_ingest_mode: bool,
}

fn deserialize_bool_with_num<'de, D>(deserializer: D) -> result::Result<bool, D::Error>
    where
        D: Deserializer<'de>,
{
    let value: Option<String> = Deserialize::deserialize(deserializer)?;
    
    Ok(value.map(|value| {
        if value == "1" {
            Ok(true)
        } else if value == "0" {
            Ok(false)
        } else {
            value.parse::<bool>()
        }
    }).transpose().map_err(|err| Error::custom(err))?.unwrap_or_default())
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
    pub fn pg_host(&self) -> Option<&str>  {
        self.pghost.as_deref()
    }

    /// Get the pg port.
    pub fn pg_port(&self) -> Option<&str>  {
        self.pgport.as_deref()
    }

    /// Get the pg user.
    pub fn pg_user(&self) -> Option<&str>  {
        self.pguser.as_deref()
    }

    /// Get the SQS url.
    pub fn sqs_queue_url(&self) -> Option<&str>  {
        self.sqs_queue_url.as_deref()
    }

    /// Get the paired ingest mode.
    pub fn paired_ingest_mode(&self) -> bool {
        self.paired_ingest_mode
    }
}