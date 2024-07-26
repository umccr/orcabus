//! This module contains event handlers for filemanager functionality.
//!

use tracing_subscriber::fmt::layer;
use tracing_subscriber::layer::SubscriberExt;
use tracing_subscriber::util::SubscriberInitExt;
use tracing_subscriber::{EnvFilter, Layer};

pub mod aws;

/// Determines which tracing formatting style to use.
#[derive(Debug, Default)]
pub enum Format {
    #[default]
    Json,
    Full,
    Compact,
    Pretty,
}

/// Initialize tracing for application code with a format.
pub fn init_tracing_with_format(format: Format) {
    let env_filter = EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info"));

    let format = match format {
        Format::Full => layer().boxed(),
        Format::Compact => layer().compact().boxed(),
        Format::Pretty => layer().pretty().boxed(),
        Format::Json => layer().json().without_time().boxed(),
    };

    tracing_subscriber::registry()
        .with(format)
        .with(env_filter)
        .init();
}

/// Initialize tracing for application code with the default format.
pub fn init_tracing() {
    init_tracing_with_format(Default::default())
}
