//! Secrets manager client wrapper.
//!

use crate::clients::aws::config::Config;
use crate::error::Error::{ParseError, SecretsManagerError};
use crate::error::Result;
use aws_credential_types::provider::ProvideCredentials;
use aws_credential_types::{provider, Credentials};
use aws_sdk_s3::error::SdkError;
use aws_sdk_secretsmanager as secretsmanager;
use aws_sdk_secretsmanager::error::DisplayErrorContext;
use aws_sdk_secretsmanager::operation::get_secret_value::GetSecretValueError;
use aws_secretsmanager_caching::output::GetSecretValueOutputDef;
use aws_secretsmanager_caching::SecretsManagerCachingClient;
use base64::prelude::Engine;
use base64::prelude::BASE64_STANDARD;
use serde::Deserialize;
use serde_json::{from_slice, from_str};
use std::error::Error;
use std::fmt::{Debug, Display, Formatter};
use std::num::NonZeroUsize;
use std::time::Duration;
use std::{fmt, result};

/// A wrapper around an S3 client which can be mocked.
pub struct Client {
    inner: SecretsManagerCachingClient,
}

impl Client {
    /// Create a new S3 client.
    pub fn new(inner: SecretsManagerCachingClient) -> Self {
        Self { inner }
    }

    /// Create an S3 client with default config.
    pub async fn with_defaults() -> Result<Self> {
        let config = Config::with_defaults().await.load();

        let client = SecretsManagerCachingClient::from_builder(
            secretsmanager::config::Builder::from(&config),
            NonZeroUsize::new(1).expect("valid non-zero usize"),
            Duration::from_secs(900),
            true,
        )
        .await
        .map_err(|err| SecretsManagerError(err.to_string()))?;

        Ok(Self::new(client))
    }

    /// Retrieve a secret value.
    pub async fn get_secret(
        &self,
        id: &str,
    ) -> result::Result<GetSecretValueOutputDef, Box<dyn Error>> {
        self.inner.get_secret_value(id, None, None, false).await
    }
}

/// Load credentials from a secrets manager secret.
#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SecretsManagerCredentials {
    access_key_id: String,
    secret_access_key: String,
}

const CREDENTIALS_NAME: &str = "credentials";

impl Debug for SecretsManagerCredentials {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        f.debug_struct(CREDENTIALS_NAME).finish()
    }
}

impl Display for SecretsManagerCredentials {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        f.write_str(CREDENTIALS_NAME)
    }
}

impl ProvideCredentials for SecretsManagerCredentials {
    fn provide_credentials<'a>(&'a self) -> provider::future::ProvideCredentials<'a>
    where
        Self: 'a,
    {
        provider::future::ProvideCredentials::new(self.load_credentials())
    }
}

impl SecretsManagerCredentials {
    /// Construct the credentials from the secret.
    pub async fn new(id: &str, client: &Client) -> Result<Self> {
        let secret = client.get_secret(id).await.map_err(|err| {
            let sdk_err: Option<&SdkError<GetSecretValueError>> = err.downcast_ref();
            let display_err = if let Some(err) = sdk_err {
                DisplayErrorContext(&err).to_string()
            } else {
                err.to_string()
            };

            SecretsManagerError(format!("no valid secret {}: {}", id, display_err))
        })?;

        let secret = if let Some(string) = secret.secret_string {
            from_str(&string)?
        } else if let Some(blob) = secret.secret_binary {
            let data = blob.into_inner();
            match from_slice(&data) {
                Ok(secret) => secret,
                Err(_) => from_slice(
                    &BASE64_STANDARD
                        .decode(data)
                        .map_err(|_| ParseError("failed to parse base64 secret".to_string()))?,
                )?,
            }
        } else {
            return Err(SecretsManagerError(format!(
                "no valid secret value found for {:?}",
                &secret.name
            )));
        };

        Ok(secret)
    }

    /// Load credentials from the secret.
    async fn load_credentials(&self) -> provider::Result {
        Ok(Credentials::new(
            self.access_key_id.clone(),
            self.secret_access_key.clone(),
            None,
            None,
            CREDENTIALS_NAME,
        ))
    }
}
