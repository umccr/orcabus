//! A mockable wrapper around SdkConfig.
//!

use aws_config::{defaults, BehaviorVersion, SdkConfig};
use aws_credential_types::provider::error::CredentialsError;
use aws_credential_types::provider::ProvideCredentials;
use aws_credential_types::Credentials;
use mockall::automock;

/// A wrapper around a config loader.
#[derive(Debug)]
pub struct Config {
    inner: SdkConfig,
}

#[automock]
impl Config {
    /// Create a new config.
    pub fn new(inner: SdkConfig) -> Self {
        Self { inner }
    }

    /// Load the config.
    pub fn load(self) -> SdkConfig {
        self.inner
    }

    /// Get the provided credentials from the config.
    pub async fn provide_credentials(&self) -> Option<Result<Credentials, CredentialsError>> {
        Some(
            self.inner
                .credentials_provider()?
                .provide_credentials()
                .await,
        )
    }

    /// Get the region used by the config.
    pub fn region(&self) -> Option<String> {
        self.inner().region().map(ToString::to_string)
    }

    pub fn inner(&self) -> &SdkConfig {
        &self.inner
    }

    /// Create a new config with default behaviour.
    pub async fn with_defaults() -> Self {
        Self::new(defaults(BehaviorVersion::latest()).load().await)
    }
}
