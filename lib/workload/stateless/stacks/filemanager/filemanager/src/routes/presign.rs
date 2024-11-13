//! Logic for the presigned url route.
//!

use serde::{Deserialize, Serialize};
use url::Url;
use utoipa::{IntoParams, ToSchema};

use crate::clients::aws::s3;
use crate::clients::aws::s3::ResponseHeaders;
use crate::database::entities::s3_object;
use crate::env::Config;
use crate::error::Error::PresignedUrlError;
use crate::error::Result;
use crate::routes::AppState;

/// Parameters for presigned URL routes.
#[derive(Serialize, Deserialize, Debug, Default, IntoParams)]
#[serde(default, rename_all = "camelCase")]
#[into_params(parameter_in = Query)]
pub struct PresignedParams {
    /// Specify the content-disposition for the presigned URLs themselves.
    /// This sets the `response-content-disposition` for the presigned `GetObject` request.
    #[param(required = false, default = "inline")]
    response_content_disposition: ContentDisposition,
}

impl PresignedParams {
    /// Create new presigned params.
    pub fn new(response_content_disposition: ContentDisposition) -> Self {
        Self {
            response_content_disposition,
        }
    }

    /// Get the response content disposition.
    pub fn response_content_disposition(&self) -> ContentDisposition {
        self.response_content_disposition
    }
}

/// Specify the content-disposition, either `inline` or `attachment`.
#[derive(Copy, Clone, Serialize, Deserialize, Debug, Default, ToSchema)]
#[serde(rename_all = "camelCase")]
pub enum ContentDisposition {
    /// Specify the content-disposition as inline.
    #[default]
    #[serde(alias = "inline")]
    Inline,
    /// Specify the content-disposition as attachment.
    #[serde(alias = "attachment")]
    Attachment,
}

/// A builder for presigned urls.
pub struct PresignedUrlBuilder<'a> {
    s3_client: &'a s3::Client,
    config: &'a Config,
    object_size: Option<i64>,
}

impl<'a> PresignedUrlBuilder<'a> {
    /// Create a builder.
    pub fn new(s3_client: &'a s3::Client, config: &'a Config) -> Self {
        Self {
            s3_client,
            config,
            object_size: None,
        }
    }

    /// Construct with the current object size.
    pub fn set_object_size(mut self, size: Option<i64>) -> Self {
        self.object_size = size;
        self
    }

    /// Create a presigned url using the key and bucket. This will not create a URL if the size
    /// is over the limit, and will instead return `None`.
    pub async fn presign_url(
        &self,
        key: &str,
        bucket: &str,
        version_id: &str,
        response_content_disposition: ContentDisposition,
        response_content_type: Option<String>,
        response_content_encoding: Option<String>,
    ) -> Result<Option<Url>> {
        let less_than_limit = if let Some(size) = self.object_size {
            if let Some(limit) = self.config.api_presign_limit() {
                u64::try_from(size).unwrap_or_default() <= limit
            } else {
                true
            }
        } else {
            true
        };

        if less_than_limit {
            let content_disposition = match response_content_disposition {
                ContentDisposition::Inline => "inline",
                ContentDisposition::Attachment => &format!("attachment; filename=\"{key}\""),
            };

            let presign = self
                .s3_client
                .presign_url(
                    key,
                    bucket,
                    version_id,
                    ResponseHeaders::new(
                        content_disposition.to_string(),
                        response_content_type,
                        response_content_encoding,
                    ),
                    self.config.api_presign_expiry(),
                )
                .await
                .map_err(|err| PresignedUrlError(err.into_service_error().to_string()))?;

            Ok(Some(presign.uri().parse()?))
        } else {
            Ok(None)
        }
    }

    /// Generate a presigned url from a database model.
    pub async fn presign_from_model(
        state: &'a AppState,
        model: s3_object::Model,
        response_content_disposition: ContentDisposition,
        response_content_type: Option<String>,
        response_content_encoding: Option<String>,
    ) -> Result<Option<Url>> {
        let builder = Self::new(state.s3_client(), state.config()).set_object_size(model.size);

        if let Some(presigned) = builder
            .presign_url(
                &model.key,
                &model.bucket,
                &model.version_id,
                response_content_disposition,
                response_content_type,
                response_content_encoding,
            )
            .await?
        {
            Ok(Some(presigned))
        } else {
            Ok(None)
        }
    }
}

#[cfg(test)]
pub(crate) mod tests {
    use aws_smithy_mocks_experimental::{mock_client, RuleMode};
    use chrono::Duration;

    use crate::clients::aws::s3;
    use crate::env::Config;
    use crate::events::aws::message::default_version_id;
    use crate::routes::list::tests::mock_get_object;

    use super::*;

    #[tokio::test]
    async fn presign() {
        let client = s3::Client::new(mock_client!(
            aws_sdk_s3,
            RuleMode::MatchAny,
            &[&mock_get_object("0", "1", b""),]
        ));
        let config = Default::default();

        let builder = PresignedUrlBuilder::new(&client, &config).set_object_size(None);
        let url = builder
            .presign_url(
                "0",
                "1",
                &default_version_id(),
                ContentDisposition::Inline,
                None,
                None,
            )
            .await
            .unwrap()
            .unwrap();

        let query = url.query().unwrap();
        assert!(query.contains("X-Amz-Expires=3600"));
        assert!(query.contains("response-content-disposition=inline"));
        assert_eq!(url.path(), "/1/0");

        let builder = PresignedUrlBuilder::new(&client, &config).set_object_size(Some(2));
        let url = builder
            .presign_url(
                "0",
                "1",
                &default_version_id(),
                ContentDisposition::Inline,
                None,
                None,
            )
            .await
            .unwrap()
            .unwrap();

        let query = url.query().unwrap();
        assert!(query.contains("X-Amz-Expires=3600"));
        assert!(query.contains("response-content-disposition=inline"));
        assert_eq!(url.path(), "/1/0");
    }

    #[tokio::test]
    async fn presign_mirror_headers() {
        let client = s3::Client::new(mock_client!(
            aws_sdk_s3,
            RuleMode::MatchAny,
            &[&mock_get_object("0", "1", b""),]
        ));
        let config = Default::default();

        let builder = PresignedUrlBuilder::new(&client, &config).set_object_size(None);
        let url = builder
            .presign_url(
                "0",
                "1",
                &default_version_id(),
                ContentDisposition::Inline,
                Some("application/json".to_string()),
                Some("gzip".to_string()),
            )
            .await
            .unwrap()
            .unwrap();

        let query = url.query().unwrap();
        assert_presigned_params(query, "inline");
        assert_eq!(url.path(), "/1/0");
    }

    #[tokio::test]
    async fn presign_attachment() {
        let client = s3::Client::new(mock_client!(
            aws_sdk_s3,
            RuleMode::Sequential,
            &[&mock_get_object("0", "1", b""),]
        ));
        let config = Default::default();

        let builder = PresignedUrlBuilder::new(&client, &config).set_object_size(None);
        let url = builder
            .presign_url(
                "0",
                "1",
                &default_version_id(),
                ContentDisposition::Attachment,
                None,
                None,
            )
            .await
            .unwrap()
            .unwrap();

        let query = url.query().unwrap();
        assert!(query.contains("X-Amz-Expires=3600"));
        assert!(query.contains("response-content-disposition=attachment%3B%20filename%3D%220%22"));
        assert_eq!(url.path(), "/1/0");
    }

    #[tokio::test]
    async fn presign_limit() {
        let client = s3::Client::new(mock_client!(
            aws_sdk_s3,
            RuleMode::Sequential,
            &[&mock_get_object("0", "1", b""),]
        ));
        let config = Config {
            api_presign_limit: Some(1),
            ..Default::default()
        };

        let builder = PresignedUrlBuilder::new(&client, &config).set_object_size(Some(2));
        let url = builder
            .presign_url(
                "0",
                "1",
                &default_version_id(),
                ContentDisposition::Inline,
                None,
                None,
            )
            .await
            .unwrap();

        assert!(url.is_none());
    }

    #[tokio::test]
    async fn presign_expiry() {
        let client = s3::Client::new(mock_client!(
            aws_sdk_s3,
            RuleMode::Sequential,
            &[&mock_get_object("0", "1", b""),]
        ));
        let config = Config {
            api_presign_expiry: Duration::seconds(500),
            ..Default::default()
        };

        let builder = PresignedUrlBuilder::new(&client, &config).set_object_size(Some(2));
        let url = builder
            .presign_url(
                "0",
                "1",
                &default_version_id(),
                ContentDisposition::Inline,
                None,
                None,
            )
            .await
            .unwrap()
            .unwrap();

        let query = url.query().unwrap();
        assert!(query.contains("X-Amz-Expires=500"));
        assert!(query.contains("response-content-disposition=inline"));
        assert_eq!(url.path(), "/1/0");
    }

    pub(crate) fn assert_presigned_params(query: &str, content_disposition: &str) {
        assert!(query.contains("X-Amz-Expires=3600"));
        assert!(query.contains(&format!(
            "response-content-disposition={content_disposition}"
        )));
        assert!(query.contains("response-content-type=application%2Fjson"));
        assert!(query.contains("response-content-encoding=gzip"));
    }
}
