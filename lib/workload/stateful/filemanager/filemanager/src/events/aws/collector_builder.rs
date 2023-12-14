#[double]
use crate::clients::aws::s3::Client as S3Client;
#[double]
use crate::clients::aws::sqs::Client as SQSClient;
use crate::env::read_env;
use crate::error::Error::{DeserializeError, SQSReceiveError};
use crate::error::Result;
use crate::events::aws::collecter::Collecter;
use crate::events::aws::FlatS3EventMessages;
use mockall_double::double;
use tracing::trace;

/// Build an AWS collector struct.
#[derive(Default, Debug)]
pub struct CollecterBuilder {
    s3_client: Option<S3Client>,
    sqs_client: Option<SQSClient>,
    sqs_url: Option<String>,
}

impl CollecterBuilder {
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
    pub fn with_sqs_url(self, url: impl Into<String>) -> Self {
        self.set_sqs_url(Some(url))
    }

    /// Set the SQS url to build with.
    pub fn set_sqs_url(mut self, url: Option<impl Into<String>>) -> Self {
        self.sqs_url = url.map(|url| url.into());
        self
    }

    /// Build a collector using the raw events.
    pub async fn build(self, raw_events: FlatS3EventMessages) -> Collecter {
        if let Some(s3_client) = self.s3_client {
            Collecter::new(s3_client, raw_events)
        } else {
            Collecter::new(S3Client::with_defaults().await, raw_events)
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

        Ok(event_messages)
    }

    /// Build a collector by manually calling receive to obtain the raw events.
    pub async fn build_receive(mut self) -> Result<Collecter> {
        let url = self.sqs_url.take();
        let url = if let Some(url) = url {
            url
        } else {
            read_env("SQS_QUEUE_URL")?
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

#[cfg(test)]
pub(crate) mod tests {
    use crate::events::aws::collecter::tests::{
        assert_collected_events, set_s3_client_expectations,
    };
    use crate::events::aws::collector_builder::CollecterBuilder;
    use crate::events::aws::tests::{expected_event_record, expected_flat_events};
    use crate::events::Collect;
    use aws_sdk_sqs::operation::receive_message::ReceiveMessageOutput;
    use aws_sdk_sqs::types::builders::MessageBuilder;
    use mockall::predicate::eq;

    use super::*;

    #[tokio::test]
    async fn receive() {
        let mut sqs_client = SQSClient::default();

        set_sqs_client_expectations(&mut sqs_client);

        let events = CollecterBuilder::receive(&sqs_client, "url").await.unwrap();

        assert_eq!(events, expected_flat_events());
    }

    #[tokio::test]
    async fn build_receive() {
        let mut sqs_client = SQSClient::default();
        let mut s3_client = S3Client::default();

        set_sqs_client_expectations(&mut sqs_client);
        set_s3_client_expectations(&mut s3_client, 2);

        let events = CollecterBuilder::default()
            .with_sqs_client(sqs_client)
            .with_s3_client(s3_client)
            .with_sqs_url("url")
            .build_receive()
            .await
            .unwrap()
            .collect()
            .await
            .unwrap();

        assert_collected_events(events);
    }

    pub(crate) fn set_sqs_client_expectations(sqs_client: &mut SQSClient) {
        sqs_client
            .expect_receive_message()
            .with(eq("url"))
            .times(1)
            .returning(move |_| Ok(expected_receive_message()));
    }

    fn expected_receive_message() -> ReceiveMessageOutput {
        ReceiveMessageOutput::builder()
            .messages(
                MessageBuilder::default()
                    .body(expected_event_record())
                    .build(),
            )
            .build()
    }
}
