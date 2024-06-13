//! This module contains the crate's error types.
//!

use dotenvy::var;
use miette::{diagnostic, Diagnostic, NamedSource, SourceOffset};
use std::fmt::{Display, Formatter};
use std::panic::Location;
use std::path::Path;
use std::{fs, result};
use thiserror::Error;

pub type Result<T> = result::Result<T, Error>;

/// Error types for the filemanager.
#[derive(Error, Debug, Diagnostic)]
pub enum ErrorKind {
    #[error("Error generating entities: {0}")]
    EntityGeneration(String),
    #[error("Missing environment variable: {0}")]
    MissingEnvironment(String),
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
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.error_kind)
    }
}

impl From<ErrorKind> for Error {
    /// Create an error with caller location to print error information.
    #[track_caller]
    fn from(error_kind: ErrorKind) -> Self {
        let loc = Location::caller();

        if let Ok(dir) = var("CARGO_MANIFEST_DIR") {
            if let Ok(source) = fs::read_to_string(Path::new(&dir).join("..").join(loc.file())) {
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
