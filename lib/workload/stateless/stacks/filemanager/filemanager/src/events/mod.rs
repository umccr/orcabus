//! This module converts storage events into database objects.
//!

use async_trait::async_trait;

use crate::error::Result;
use crate::events::aws::Events;

pub mod aws;

/// This trait processes raw events into a common type that can easily be consumed by the database.
#[async_trait]
pub trait Collect {
    /// Collect into events.
    async fn collect(self) -> Result<EventSourceType>;
}

/// The type of event.
#[derive(Debug)]
#[non_exhaustive]
pub enum EventSourceType {
    S3(Events),
}
