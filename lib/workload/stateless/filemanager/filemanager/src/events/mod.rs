//! This module handles converting storage events into database objects
//!

use async_trait::async_trait;

use crate::error::Result;
use crate::events::s3::Events;

pub mod s3;

/// This trait processes raw events into a common type that can easily be consumed by the database.
#[async_trait]
pub trait Collect {
    /// Collect into events.
    async fn collect(self) -> Result<EventType>;
}

/// The type of event.
#[derive(Debug)]
#[non_exhaustive]
pub enum EventType {
    S3(Events),
}
