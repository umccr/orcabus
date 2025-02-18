//! A module for generating RDS IAM credentials.
//!

use std::iter::empty;
use std::time::{Duration, SystemTime};

use async_trait::async_trait;
use aws_sigv4::http_request::SignatureLocation::QueryParams;
use aws_sigv4::http_request::{sign, SignableBody, SignableRequest, SigningSettings};
use aws_sigv4::sign::v4::SigningParams;
use url::Url;

use crate::clients::aws::config::Config;
use crate::database::CredentialGenerator;
use crate::env::Config as EnvConfig;
use crate::error::Error::CredentialGeneratorError;
use crate::error::Result;

/// Number of seconds that the IAM credentials expire in.
/// Equals the max Lambda timeout.
pub const CREDENTIAL_EXPIRES_IN_SECONDS: u64 = 900;

/// The builder for the IamGenerator.
#[derive(Debug, Default)]
pub struct IamGeneratorBuilder {
    config: Option<Config>,
    host: Option<String>,
    port: Option<u16>,
    user: Option<String>,
}

impl IamGeneratorBuilder {
    /// Set the config. If not set, uses the default config.
    pub fn with_config(mut self, config: Config) -> Self {
        self.config = Some(config);
        self
    }

    /// Build with a host. If not set, tries to source this from PGHOST.
    pub fn with_host(mut self, host: String) -> Self {
        self.host = Some(host);
        self
    }

    /// Build with a port. If not set, tries to source this from PGPORT.
    pub fn with_port(mut self, port: u16) -> Self {
        self.port = Some(port);
        self
    }

    /// Build with a user. If not set, tries to source this from PGUSER.
    pub fn with_user(mut self, user: String) -> Self {
        self.user = Some(user);
        self
    }

    /// Build the credential generator.
    pub async fn build(self, env_config: &EnvConfig) -> Result<IamGenerator> {
        let config = if let Some(config) = self.config {
            config
        } else {
            Config::with_defaults().await
        };

        let host =
            EnvConfig::value_or_else(self.host.as_deref(), env_config.pg_host())?.to_string();
        let port = EnvConfig::value_or_else(self.port, env_config.pg_port())?;
        let user =
            EnvConfig::value_or_else(self.user.as_deref(), env_config.pg_user())?.to_string();

        Ok(IamGenerator::new(config, host, port, user))
    }
}

/// A struct to generate RDS IAM database credentials.
#[derive(Debug)]
pub struct IamGenerator {
    config: Config,
    host: String,
    port: u16,
    user: String,
}

impl IamGenerator {
    /// Create a new credential generator.
    pub fn new(config: Config, host: String, port: u16, user: String) -> Self {
        Self {
            config,
            host,
            port,
            user,
        }
    }

    /// Create a new credential generator with default config.
    pub async fn with_defaults(host: String, port: u16, user: String) -> Self {
        Self::new(Config::with_defaults().await, host, port, user)
    }

    /// Get the config.
    pub fn config(&self) -> &Config {
        &self.config
    }

    /// Get the host address.
    pub fn host(&self) -> &str {
        &self.host
    }

    /// Get the port.
    pub fn port(&self) -> u16 {
        self.port
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
        signing_settings.expires_in = Some(Duration::from_secs(CREDENTIAL_EXPIRES_IN_SECONDS));
        signing_settings.signature_location = QueryParams;

        let signing_params = SigningParams::builder()
            .identity(&identity)
            .region(&region)
            .name("rds-db")
            .time(SystemTime::now())
            .settings(signing_settings)
            .build()
            .map_err(|err| CredentialGeneratorError(err.to_string()))?;

        let url = format!(
            "https://{}:{}/?Action=connect&DBUser={}",
            self.host, self.port, self.user
        );

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

#[async_trait]
impl CredentialGenerator for IamGenerator {
    async fn generate_password(&self) -> Result<String> {
        self.generate_iam_token().await
    }
}

#[cfg(test)]
mod tests {
    use crate::database::aws::credentials::Config;
    use std::borrow::Cow;
    use std::collections::HashMap;
    use std::future::Future;

    use super::*;
    use aws_credential_types::Credentials;

    #[tokio::test]
    async fn generate_iam_token() {
        test_generate_iam_token(|config| async {
            IamGeneratorBuilder::default()
                .with_config(config)
                .with_host("127.0.0.1".to_string())
                .with_port(5432)
                .with_user("filemanager".to_string())
                .build(&Default::default())
                .await
                .unwrap()
        })
        .await;
    }

    #[tokio::test]
    async fn generate_iam_token_env() {
        let env_config = EnvConfig {
            pghost: Some("127.0.0.1".to_string()),
            pgport: Some(5432),
            pguser: Some("filemanager".to_string()),
            ..Default::default()
        };

        test_generate_iam_token(|config| async {
            IamGeneratorBuilder::default()
                .with_config(config)
                .build(&env_config)
                .await
                .unwrap()
        })
        .await;
    }

    async fn test_generate_iam_token<F, Fut>(create_generator: F)
    where
        F: FnOnce(Config) -> Fut,
        Fut: Future<Output = IamGenerator>,
    {
        let config = Config::from_provider(Credentials::new(
            "access-key-id",
            "secret-access-key",
            Some("session-token".to_string()),
            Some(SystemTime::UNIX_EPOCH),
            "provider-name",
        ))
        .await;

        let generator = create_generator(config).await;
        // Add the scheme back in so that the url can be parsed.
        let mut url = "https://".to_string();
        url.push_str(&generator.generate_iam_token().await.unwrap());
        let url = Url::parse(&url).unwrap();

        assert_eq!(url.host().unwrap().to_string(), "127.0.0.1");
        assert_eq!(url.port().unwrap(), 5432);
        assert_eq!(url.path(), "/");

        let queries: HashMap<Cow<str>, Cow<str>> = HashMap::from_iter(url.query_pairs());

        assert_eq!(queries.get("Action"), Some(&"connect".into()));
        assert_eq!(queries.get("DBUser"), Some(&"filemanager".into()));
        assert_eq!(
            queries.get("X-Amz-Security-Token"),
            Some(&"session-token".into())
        );

        let credentials = queries.get("X-Amz-Credential").unwrap();

        assert!(credentials.contains("access-key-id"));
        assert!(credentials.contains("ap-southeast-2"));
        assert!(credentials.contains("rds-db"));
    }
}
