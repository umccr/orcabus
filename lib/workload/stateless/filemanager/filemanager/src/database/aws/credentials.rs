//! A module for generating RDS IAM credentials.
//!

use std::iter::empty;
use std::time::{Duration, SystemTime};

use aws_sigv4::http_request::SignatureLocation::QueryParams;
use aws_sigv4::http_request::{sign, SignableBody, SignableRequest, SigningSettings};
use aws_sigv4::sign::v4::SigningParams;
use mockall_double::double;
use url::Url;

#[double]
use crate::clients::aws::config::Config;
use crate::error::Error::CredentialGeneratorError;
use crate::error::Result;

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
    pub async fn with_defaults(host: String, user: String) -> Self {
        Self::new(Config::with_defaults().await, host, user)
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
            .ok_or_else(|| CredentialGeneratorError("missing region".to_string()))?;

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

        let mut url = Url::parse(&url).map_err(|err| CredentialGeneratorError(err.to_string()))?;
        for (name, value) in signing_instructions.params() {
            url.query_pairs_mut().append_pair(name, value);
        }

        Ok(url.to_string().split_off("https://".len()))
    }
}

#[cfg(test)]
mod tests {
    use std::borrow::Cow;
    use std::collections::HashMap;

    use aws_credential_types::Credentials;

    use crate::clients::aws::config::MockConfig;

    use super::*;

    #[tokio::test]
    async fn generate_iam_token() {
        let mut config = MockConfig::default();

        config.expect_provide_credentials().once().returning(|| {
            Some(Ok(Credentials::new(
                "access_key_id",
                "secret_access_key",
                Some("session_token".to_string()),
                Some(SystemTime::UNIX_EPOCH),
                "provider_name",
            )))
        });
        config
            .expect_region()
            .once()
            .returning(|| Some("ap-southeast-2".to_string()));

        let generator =
            IamCredentialGenerator::new(config, "127.0.0.1".to_string(), "filemanager".to_string());

        // Add the scheme back in so that the url can be parsed.
        let mut url = "https://".to_string();
        url.push_str(&generator.generate_iam_token().await.unwrap());
        let url = Url::parse(&url).unwrap();

        assert_eq!(url.host().unwrap().to_string(), "127.0.0.1");
        assert_eq!(url.path(), "/");

        let queries: HashMap<Cow<str>, Cow<str>> = HashMap::from_iter(url.query_pairs());

        assert_eq!(queries.get("Action"), Some(&"connect".into()));
        assert_eq!(queries.get("DBUser"), Some(&"filemanager".into()));
        assert_eq!(
            queries.get("X-Amz-Security-Token"),
            Some(&"session_token".into())
        );

        let credentials = queries.get("X-Amz-Credential").unwrap();

        assert!(credentials.contains("access_key_id"));
        assert!(credentials.contains("ap-southeast-2"));
        assert!(credentials.contains("rds-db"));
    }
}
