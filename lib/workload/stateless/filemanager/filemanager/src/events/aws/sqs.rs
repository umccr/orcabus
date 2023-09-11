use aws_sdk_sqs::Client;
use futures::future::join_all;
use tracing::trace;
use crate::error::Error::{ConfigError, DbClientError, SQSDeserializeError, SQSReceiveError};
use crate::error::Result;
use crate::events::aws::S3EventMessage;

#[derive(Debug)]
pub struct SQS {
    sqs_client: Client,
    sqs_url: String,
}

impl SQS {
    pub fn new(sqs_client: Client, sqs_url: String) -> Self {
        Self {
            sqs_client,
            sqs_url,
        }
    }

    pub async fn with_default_client() -> Result<Self> {
        let config = aws_config::from_env()
            .endpoint_url(
                std::env::var("ENDPOINT_URL").map_err(|err| ConfigError(err.to_string()))?,
            )
            .load()
            .await;

        Ok(Self {
            sqs_client: Client::new(&config),
            sqs_url: std::env::var("SQS_QUEUE_URL")
                .map_err(|err| DbClientError(err.to_string()))?,
        })
    }

    // TODO: Two possible event types, should be handled differently: PUT and DELETE
    pub async fn receive(&self) -> Result<Vec<S3EventMessage>> {
        let rcv_message_output = self
            .sqs_client
            .receive_message()
            .queue_url(&self.sqs_url)
            .send()
            .await
            .map_err(|err| SQSReceiveError(err.into_service_error().to_string()))?;

        join_all(
            rcv_message_output
                .messages
                .unwrap_or_default()
                .into_iter()
                .map(|message| async move {
                    trace!(message = ?message, "got the message");

                    if let Some(body) = message.body() {
                        serde_json::from_str(body)
                            .map_err(|err| SQSDeserializeError(err.to_string()))
                    } else {
                        Err(SQSReceiveError("No body in SQS message".to_string()))
                    }
                }),
        )
            .await
            .into_iter()
            .collect::<Result<Vec<S3EventMessage>>>()
    }
}
