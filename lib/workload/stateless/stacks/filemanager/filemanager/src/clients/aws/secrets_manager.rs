//! Secrets manager client wrapper.
//!

use crate::clients::aws::config::Config;
use crate::error::Error::SecretsManagerError;
use crate::error::Result;
use aws_credential_types::provider::ProvideCredentials;
use aws_credential_types::{provider, Credentials};
use aws_sdk_s3::error::SdkError;
use aws_sdk_secretsmanager as secretsmanager;
use aws_sdk_secretsmanager::operation::get_secret_value::{
    GetSecretValueError, GetSecretValueOutput,
};
use base64::prelude::Engine;
use base64::prelude::BASE64_STANDARD;
use serde::Deserialize;
use serde_json::{from_slice, from_str};
use std::fmt::{Debug, Display, Formatter};
use std::{fmt, result};

/// A wrapper around an S3 client which can be mocked.
#[derive(Debug)]
pub struct Client {
    inner: secretsmanager::Client,
}

impl Client {
    /// Create a new S3 client.
    pub fn new(inner: secretsmanager::Client) -> Self {
        Self { inner }
    }

    /// Create an S3 client with default config.
    pub async fn with_defaults() -> Self {
        Self::new(secretsmanager::Client::new(
            &Config::with_defaults().await.load(),
        ))
    }

    /// Retrieve a secret value.
    pub async fn get_secret(
        &self,
        id: &str,
    ) -> result::Result<GetSecretValueOutput, SdkError<GetSecretValueError>> {
        self.inner.get_secret_value().secret_id(id).send().await
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
    pub async fn new(id: &str) -> Result<Self> {
        let client = Client::with_defaults().await;

        let err = || SecretsManagerError(format!("no valid secret value found for {}", id));
        let secret = client
            .get_secret(id)
            .await
            .map_err(|err| SecretsManagerError(err.to_string()))?;

        let secret = if let Some(string) = secret.secret_string {
            from_str(&string)?
        } else if let Some(blob) = secret.secret_binary {
            let data = blob.into_inner();
            match from_slice(&data) {
                Ok(secret) => secret,
                Err(_) => from_slice(&BASE64_STANDARD.decode(data).map_err(|_| err())?)?,
            }
        } else {
            return Err(err());
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
