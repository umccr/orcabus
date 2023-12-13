//! Event handlers for AWS, such as Lambda event handlers.
//!

#[double]
use crate::clients::aws::s3::Client as S3Client;
#[double]
use crate::clients::aws::sqs::Client as SQSClient;
use crate::database::aws::ingester::Ingester;
use crate::database::{Client, Ingest};
use crate::events::aws::collector_builder::CollecterBuilder;
use crate::events::aws::FlatS3EventMessages;
use crate::events::Collect;
use aws_lambda_events::sqs::SqsEvent;
use lambda_runtime::Error;
use mockall_double::double;
use tracing::trace;

/// Handle SQS events by manually calling the SQS receive function. This is meant
/// to be run through something like API gateway to manually invoke ingestion.
pub async fn receive_and_ingest(
    s3_client: S3Client,
    sqs_client: SQSClient,
    sqs_url: Option<impl Into<String>>,
    database_client: Option<Client>,
) -> Result<Ingester, Error> {
    let events = CollecterBuilder::default()
        .with_s3_client(s3_client)
        .with_sqs_client(sqs_client)
        .set_sqs_url(sqs_url)
        .build_receive()
        .await?
        .collect()
        .await?;

    let mut ingester = if let Some(database_client) = database_client {
        Ingester::new(database_client)
    } else {
        Ingester::with_defaults().await?
    };

    ingester.ingest(events).await?;

    Ok(ingester)
}

/// Handle SQS events that through an SqsEvent.
pub async fn ingest_event(
    event: SqsEvent,
    s3_client: S3Client,
    database_client: Option<Client>,
) -> Result<Ingester, Error> {
    trace!("received event: {:?}", event);

    let events: FlatS3EventMessages = event
        .records
        .into_iter()
        .filter_map(|event| {
            event.body.map(|body| {
                let body: FlatS3EventMessages = serde_json::from_str(&body)?;
                Ok(body)
            })
        })
        .collect::<Result<Vec<FlatS3EventMessages>, Error>>()?
        .into();

    trace!("flattened events: {:?}", events);

    let events = CollecterBuilder::default()
        .with_s3_client(s3_client)
        .build(events)
        .await
        .collect()
        .await?;

    trace!("ingesting events: {:?}", events);

    let mut ingester = if let Some(database_client) = database_client {
        Ingester::new(database_client)
    } else {
        Ingester::with_defaults().await?
    };

    trace!("ingester: {:?}", ingester);
    ingester.ingest(events).await?;

    Ok(ingester)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::database::aws::ingester::tests::assert_deleted;
    use crate::events::aws::collecter::tests::set_s3_client_expectations;
    use crate::events::aws::collector_builder::tests::set_sqs_client_expectations;
    use crate::events::aws::tests::expected_event_record;
    use aws_lambda_events::sqs::SqsMessage;
    use sqlx::PgPool;

    #[sqlx::test(migrations = "../database/migrations")]
    async fn test_receive_and_ingest(pool: PgPool) {
        let mut sqs_client = SQSClient::default();
        let mut s3_client = S3Client::default();

        set_sqs_client_expectations(&mut sqs_client);
        set_s3_client_expectations(&mut s3_client, 2);

        let ingester =
            receive_and_ingest(s3_client, sqs_client, Some("url"), Some(Client::new(pool)))
                .await
                .unwrap();

        let result = sqlx::query("select * from object")
            .fetch_one(ingester.client().pool())
            .await
            .unwrap();

        assert_deleted(result);
    }

    #[sqlx::test(migrations = "../database/migrations")]
    async fn test_ingest_event(pool: PgPool) {
        let mut s3_client = S3Client::default();

        set_s3_client_expectations(&mut s3_client, 2);

        let event = SqsEvent {
            records: vec![SqsMessage {
                body: Some(expected_event_record()),
                ..Default::default()
            }],
        };

        let ingester = ingest_event(event, s3_client, Some(Client::new(pool)))
            .await
            .unwrap();

        let result = sqlx::query("select * from object")
            .fetch_one(ingester.client().pool())
            .await
            .unwrap();

        assert_deleted(result);
    }
}
