#[double]
use crate::clients::aws::s3::Client as S3Client;
#[double]
use crate::clients::aws::sqs::Client as SQSClient;
use crate::database::aws::ingester::Ingester;
use crate::database::Ingest;
use crate::events::aws::collector_builder::CollecterBuilder;
use crate::events::aws::FlatS3EventMessages;
use crate::events::Collect;
use aws_lambda_events::sqs::SqsEvent;
use lambda_runtime::{Error, LambdaEvent};
use mockall_double::double;
use tracing::trace;

/// Handle SQS events by manually calling the SQS receive function. This is meant
/// to be run through something like API gateway to manually invoke ingestion.
pub async fn receive_and_ingest(
    s3_client: S3Client,
    sqs_client: SQSClient,
    sqs_url: Option<impl Into<String>>,
) -> Result<(), Error> {
    let events = CollecterBuilder::default()
        .with_s3_client(s3_client)
        .with_sqs_client(sqs_client)
        .set_sqs_url(sqs_url)
        .build_receive()
        .await?
        .collect()
        .await?;

    let mut ingester = Ingester::with_defaults().await?;

    ingester.ingest(events).await?;

    Ok(())
}

/// Handle SQS events that are passed directly to a lambda function via an LambdEvent.
pub async fn ingest_event(event: LambdaEvent<SqsEvent>, s3_client: S3Client) -> Result<(), Error> {
    trace!("received event: {:?}", event);

    let events: FlatS3EventMessages = event
        .payload
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

    let mut ingester = Ingester::with_defaults().await?;
    trace!("ingester: {:?}", ingester);
    ingester.ingest(events).await?;

    Ok(())
}
