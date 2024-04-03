//! A module for generating RDS IAM credentials.
//!

use std::iter::empty;
use std::time::{Duration, SystemTime};

use crate::clients::aws::config::Config;
use crate::error::Error::CredentialGeneratorError;
use crate::error::Result;
use aws_sigv4::http_request::SignatureLocation::QueryParams;
use aws_sigv4::http_request::{sign, SignableBody, SignableRequest, SigningSettings};
use aws_sigv4::sign::v4::SigningParams;

#[derive(Debug)]
pub struct IamCredentialGenerator {
    config: Config,
    host: String,
    user: String,
}

impl IamCredentialGenerator {
    /// Create a new credential generator.
    pub fn new(config: Config, host: String, user: String) -> Self {
        Self { config, host, user }
    }

    /// Create a new credential generator with default config.
    pub async fn with_defaults(address: String, user: String) -> Self {
        Self::new(Config::with_defaults().await, address, user)
    }

    /// Get the config.
    pub fn config(&self) -> &Config {
        &self.config
    }

    /// Get the host address.
    pub fn host(&self) -> &str {
        &self.host
    }

    /// Get the user.
    pub fn user(&self) -> &str {
        &self.user
    }

    /// Generate an RDS IAM token which can be used as the password to connect to the RDS database.
    pub async fn generate_iam_token(&self) -> Result<String> {
        let identity = self
            .config
            .provide_credentials()
            .await
            .ok_or_else(|| CredentialGeneratorError("missing credentials provider".to_string()))?
            .map_err(|err| CredentialGeneratorError(err.to_string()))?
            .into();
        let region = self
            .config
            .region()
            .ok_or_else(|| CredentialGeneratorError("missing region".to_string()))?
            .to_string();

        let mut signing_settings = SigningSettings::default();
        signing_settings.expires_in = Some(Duration::from_secs(900));
        signing_settings.signature_location = QueryParams;

        let signing_params = SigningParams::builder()
            .identity(&identity)
            .region(&region)
            .name("rds-db")
            .time(SystemTime::now())
            .settings(signing_settings)
            .build()
            .map_err(|err| CredentialGeneratorError(err.to_string()))?;

        let url = format!("https://{}/?Action=connect&DBUser={}", self.host, self.user);

        let signable_request = SignableRequest::new("GET", &url, empty(), SignableBody::Bytes(&[]))
            .map_err(|err| CredentialGeneratorError(err.to_string()))?;

        let (signing_instructions, _) = sign(signable_request, &signing_params.into())
            .map_err(|err| CredentialGeneratorError(err.to_string()))?
            .into_parts();

        let mut url = url::Url::parse(&url).unwrap();
        for (name, value) in signing_instructions.params() {
            url.query_pairs_mut().append_pair(name, value);
        }

        Ok(url.to_string().split_off("https://".len()))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn generate_iam_token() {
        let generator = IamCredentialGenerator::with_defaults(
            "127.0.0.1".to_string(),
            "filemanager".to_string(),
        )
        .await;
        let creds = generator.generate_iam_token().await;
        println!("{:#?}", creds);
    }
}
