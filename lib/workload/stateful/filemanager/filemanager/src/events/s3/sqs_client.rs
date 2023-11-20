use std::env;

use aws_sdk_sqs::{config, Client};
use tracing::trace;

use crate::error::Error::{DbClientError, DeserializeError, SQSReceiveError};
use crate::error::Result;
use crate::events::s3::FlatS3EventMessages;

/// A wrapper around an SQS client.
#[derive(Debug)]
pub struct SQS {
    sqs_client: Client,
    sqs_url: String,
}

impl SQS {
    /// Create a new SQS client wrapper.
    pub fn new(sqs_client: Client, sqs_url: String) -> Self {
        Self {
            sqs_client,
            sqs_url,
        }
    }


    /// Create with a default SQS client.
    pub async fn with_default_client() -> Result<Self> {
        let config = aws_config::from_env().load().await;
        let mut config = config::Builder::from(&config);

        if let Ok(endpoint) = env::var("ENDPOINT_URL") {
            trace!("Using endpoint {}", endpoint);
            config = config.endpoint_url(endpoint);
        }

        Ok(Self {
            sqs_client: Client::from_conf(config.build()),
            sqs_url: std::env::var("SQS_QUEUE_URL")
                .map_err(|err| DbClientError(err.to_string()))?,
        })
    }

    /// Manually call the receive function to retrieve events from the SQS queue.
    pub async fn receive(&self) -> Result<FlatS3EventMessages> {
        let rcv_message_output = self
            .sqs_client
            .receive_message()
            .queue_url(&self.sqs_url)
            .send()
            .await
            .map_err(|err| SQSReceiveError(err.into_service_error().to_string()))?;

        let event_messages: FlatS3EventMessages = rcv_message_output
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
}
