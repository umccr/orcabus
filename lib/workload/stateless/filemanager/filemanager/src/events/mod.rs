//! This module handles converting storage events into database objects
//!

pub mod aws;

use crate::events::aws::Events;
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
