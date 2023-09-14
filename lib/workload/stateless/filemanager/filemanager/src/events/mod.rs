//! This module handles converting storage events into database objects
//!

pub mod s3;

use crate::events::s3::Events;
use crate::error::Result;

/// This trait processes raw events into a common type that can easily be consumed by the database.
pub trait Collect {
    /// Collect into events.
    fn collect(self) -> Result<EventType>;
}

/// The type of event.
#[derive(Debug)]
#[non_exhaustive]
pub enum EventType {
    S3(Events),
}
