use crate::clients::config::Config;
use aws_sdk_sqs as sqs;
use aws_sdk_sqs::error::SdkError;
use aws_sdk_sqs::operation::receive_message::{ReceiveMessageError, ReceiveMessageOutput};
use mockall::automock;
use std::result;

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
    pub async fn default() -> Self {
        Self::new(sqs::Client::new(&Config::default().load().await))
    }

    /// Execute the `ReceiveMessage` operation.
    pub async fn receive_message(&self) -> Result<ReceiveMessageOutput, ReceiveMessageError> {
        self.inner.receive_message().send().await
    }
}
