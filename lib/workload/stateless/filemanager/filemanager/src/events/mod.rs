//! This module handles converting storage events into database objects
//!

pub mod aws;

use crate::events::aws::FlatS3EventMessages;

/// The type of event.
#[derive(Debug)]
#[non_exhaustive]
pub enum EventType {
    S3(FlatS3EventMessages),
}
