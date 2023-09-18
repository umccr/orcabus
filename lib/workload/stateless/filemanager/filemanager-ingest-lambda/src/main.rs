use aws_lambda_events::sqs::SqsEvent;
use lambda_runtime::{run, service_fn, Error, LambdaEvent};
use tracing::{info, trace};

use filemanager::database::s3::ingester::Ingester;
use filemanager::events::s3::s3::S3;
use filemanager::events::s3::FlatS3EventMessages;

/// Handle SQS events.
async fn event_handler(event: LambdaEvent<SqsEvent>) -> Result<(), Error> {
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

    let s3 = S3::with_defaults().await?;
    let events = s3.update_events(events).await?;

    let mut ingester = Ingester::new_with_defaults().await?;

    let events = events.into();
    trace!("ingesting events: {:?}", events);

    ingester.ingest_events(events).await?;

    Ok(())
}

#[tokio::main]
async fn main() -> Result<(), Error> {
    tracing_subscriber::fmt()
        .json()
        .with_target(false)
        .without_time()
        .init();

    run(service_fn(event_handler)).await
}
