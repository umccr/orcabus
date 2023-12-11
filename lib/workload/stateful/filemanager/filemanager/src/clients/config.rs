use aws_config::{defaults, BehaviorVersion, ConfigLoader, SdkConfig};

/// A wrapper around a config loader.
#[derive(Debug)]
pub struct Config {
    inner: ConfigLoader,
}

impl Config {
    /// Load the config.
    pub async fn load(self) -> SdkConfig {
        self.inner.load().await
    }
}

impl Default for Config {
    fn default() -> Self {
        Self {
            inner: defaults(BehaviorVersion::latest()),
        }
    }
}
