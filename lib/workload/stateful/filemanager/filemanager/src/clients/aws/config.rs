use aws_config::{defaults, BehaviorVersion, ConfigLoader, SdkConfig};
use mockall::automock;

/// A wrapper around a config loader.
#[derive(Debug)]
pub struct Config {
    inner: ConfigLoader,
}

#[automock]
impl Config {
    /// Create a new config.
    pub fn new(inner: ConfigLoader) -> Self {
        Self { inner }
    }

    /// Load the config.
    pub async fn load(self) -> SdkConfig {
        self.inner.load().await
    }

    /// Create a new config with default behaviour.
    pub fn with_defaults() -> Self {
        Self::new(defaults(BehaviorVersion::latest()))
    }
}
