use thiserror::Error;
use std::result;

pub type Result<T> = result::Result<T, Error>;

#[derive(Error, Debug)]
pub enum Error {
    /// File not found by id.
    #[error("file not found: `{0}`")]
    NotFound(String),
    /// File operation unauthorized
    #[error("unauthorized: `{0}`")]
    Unauthorized(String),
}