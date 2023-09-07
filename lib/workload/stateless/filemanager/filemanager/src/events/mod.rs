//! This module handles ingesting storage events into the file manager database.
//!

pub mod s3;

use crate::file::File;

/// Convert into a file struct which can be inserted into the database.
pub trait IntoFile {
    fn into_file(self) -> File;
}

/// Ingest files from a storage backend.
pub trait ReceiveFiles {
    fn receive_files(&self) -> Vec<File>;
}

/// The type of ingester.
pub enum Receiver {
    S3(s3::Receiver),
}
