use std::result;

use aws_sdk_sqs as sqs;
use aws_sdk_sqs::error::SdkError;
use aws_sdk_sqs::operation::receive_message::{ReceiveMessageError, ReceiveMessageOutput};
use aws_sdk_sqs::operation::send_message::{SendMessageError, SendMessageOutput};
use mockall::automock;

use crate::clients::aws::config::Config;

pub type Result<T, E> = result::Result<T, SdkError<E>>;

/// A wrapper around an SQS client which can be mocked.
#[derive(Debug)]
pub struct Client {
    inner: sqs::Client,
}

#[automock]
impl Client {
    /// Create a new S3 client.
    pub fn new(inner: sqs::Client) -> Self {
        Self { inner }
    }

    /// Create an SQS client with default config.
    pub async fn with_defaults() -> Self {
        Self::new(sqs::Client::new(&Config::with_defaults().load().await))
    }

    /// Execute the `ReceiveMessage` operation.
    pub async fn receive_message(
        &self,
        queue_url: &str,
    ) -> Result<ReceiveMessageOutput, ReceiveMessageError> {
        self.inner
            .receive_message()
            .queue_url(queue_url)
            .send()
            .await
    }

    /// Execute the `SendMessage` operation.
    pub async fn send_message(
        &self,
        queue_url: &str,
    ) -> Result<SendMessageOutput, SendMessageError> {
        self.inner.send_message().queue_url(queue_url).send().await
    }
}
