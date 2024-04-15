//! The filemanager crate is the primary library code used by other crates to handle filemanager
//! logic.
//!

use crate::error::Error::MissingEnvironmentVariable;
use crate::error::Result;

pub mod clients;
pub mod database;
pub mod error;
pub mod events;
pub mod handlers;
pub mod uuid;

/// Read an environment variable into a string.
pub fn read_env<K: AsRef<str>>(key: K) -> Result<String> {
    std::env::var(key.as_ref()).map_err(|err| MissingEnvironmentVariable(err.to_string()))
}
