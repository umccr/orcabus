//! Database logic for AWS events.
//!

pub mod ingester;

pub mod credentials;
#[cfg(feature = "migrate")]
pub mod migration;
