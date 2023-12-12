#[double]
use crate::clients::s3::Client as S3Client;
#[double]
use crate::clients::sqs::Client as SQSClient;
use crate::error::Error::{DeserializeError, MissingSQSUrl, SQSReceiveError};
use crate::error::Result;
use crate::events::s3::collecter::Collector;
use crate::events::s3::FlatS3EventMessages;
use mockall_double::double;
use std::env;
use tracing::trace;

/// Build an AWS collector struct.
#[derive(Default, Debug)]
pub struct CollectorBuilder {
    s3_client: Option<S3Client>,
    sqs_client: Option<SQSClient>,
    sqs_url: Option<String>,
}

impl CollectorBuilder {
    /// Build with the S3 client.
    pub fn with_s3_client(mut self, client: S3Client) -> Self {
        self.s3_client = Some(client);
        self
    }

    /// Build with the SQS client.
    pub fn with_sqs_client(mut self, client: SQSClient) -> Self {
        self.sqs_client = Some(client);
        self
    }

    /// Build with the SQS url.
    pub fn with_sqs_url(mut self, url: String) -> Self {
        self.sqs_url = Some(url);
        self
    }

    /// Build a collector using the raw events.
    pub async fn build(self, raw_events: FlatS3EventMessages) -> Collector {
        if let Some(s3_client) = self.s3_client {
            Collector::new(s3_client, raw_events)
        } else {
            Collector::new(S3Client::with_defaults().await, raw_events)
        }
    }

    /// Manually call the receive function to retrieve events from the SQS queue.
    pub async fn receive(client: &SQSClient, url: &str) -> Result<FlatS3EventMessages> {
        let message_output = client
            .receive_message(url)
            .await
            .map_err(|err| SQSReceiveError(err.into_service_error().to_string()))?;

        let event_messages: FlatS3EventMessages = message_output
            .messages
            .unwrap_or_default()
            .into_iter()
            .map(|message| {
                trace!(message = ?message, "got the message");

                if let Some(body) = message.body() {
                    serde_json::from_str(body).map_err(|err| DeserializeError(err.to_string()))
                } else {
                    Err(SQSReceiveError("No body in SQS message".to_string()))
                }
            })
            .collect::<Result<Vec<FlatS3EventMessages>>>()?
            .into();

        Ok(event_messages.sort_and_dedup())
    }

    /// Build a collector by manually calling receive to obtain the raw events.
    pub async fn build_receive(mut self) -> Result<Collector> {
        let url = self.sqs_url.take();
        let url = if let Some(url) = url {
            url
        } else {
            env::var("SQS_QUEUE_URL").map_err(|err| MissingSQSUrl(err.to_string()))?
        };

        let client = self.sqs_client.take();
        if let Some(sqs_client) = &client {
            Ok(self.build(Self::receive(sqs_client, &url).await?).await)
        } else {
            Ok(self
                .build(Self::receive(&SQSClient::with_defaults().await, &url).await?)
                .await)
        }
    }
}
