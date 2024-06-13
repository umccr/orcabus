//! This module contains the crate's error types.
//!

use std::result;
use thiserror::Error;

pub type Result<T> = result::Result<T, Error>;

/// Error types for the filemanager.
#[derive(Error, Debug)]
pub enum Error {
    #[error("Error generating entities: `{0}`")]
    EntityGeneration(String),
    #[error("Missing environment variable: `{0}`")]
    MissingEnvironment(String),
}