//! This module contains the crate's error types.
//!

use std::fmt::{Display, Formatter};
use std::fs::read_to_string;
use std::panic::Location;
use std::{fmt, io, result};

use miette::{diagnostic, Diagnostic, NamedSource, SourceOffset};
use thiserror::Error;

use crate::error::ErrorKind::IoError;
use crate::workspace_path;

pub type Result<T> = result::Result<T, Error>;

/// Error types for the filemanager.
#[derive(Error, Debug)]
pub enum ErrorKind {
    #[error("Error generating entities: {0}")]
    EntityGeneration(String),
    #[error("Error generating OpenAPI definitions: {0}")]
    OpenAPIGeneration(String),
    #[error("Missing or incorrect environment variables: {0}")]
    LoadingEnvironment(String),
    #[error("io error: {0}")]
    IoError(io::Error),
}

#[derive(Error, Debug, Diagnostic)]
#[diagnostic(help("Is a local database instance running with environment variables set?"))]
pub struct Error {
    error_kind: ErrorKind,
    #[source_code]
    src: Option<NamedSource<String>>,
    #[label]
    label: Option<SourceOffset>,
}

impl Display for Error {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.error_kind)
    }
}

impl From<io::Error> for Error {
    #[track_caller]
    fn from(error: io::Error) -> Self {
        Self::from(IoError(error))
    }
}

impl From<ErrorKind> for Error {
    /// Create an error with caller location to print error information.
    #[track_caller]
    fn from(error_kind: ErrorKind) -> Self {
        let loc = Location::caller();

        if let Some(path) = workspace_path() {
            if let Ok(source) = read_to_string(path.join(loc.file())) {
                let offset = SourceOffset::from_location(
                    source.as_str(),
                    loc.line() as usize,
                    loc.column() as usize,
                );

                return Self::new(
                    error_kind,
                    Some(NamedSource::new(loc.file(), source)),
                    Some(offset),
                );
            }
        }

        Self::new(error_kind, None, None)
    }
}

impl Error {
    /// Create a new error.
    pub fn new(
        error_kind: ErrorKind,
        src: Option<NamedSource<String>>,
        label: Option<SourceOffset>,
    ) -> Self {
        Self {
            error_kind,
            src,
            label,
        }
    }
}
