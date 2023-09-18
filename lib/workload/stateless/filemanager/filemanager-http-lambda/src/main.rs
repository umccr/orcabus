use filemanager::database::s3::ingester::Ingester;
use filemanager::events::s3::s3::S3;
use filemanager::events::s3::sqs::SQS;
use lambda_http::Error;
use lambda_runtime::{run, service_fn, LambdaEvent};

/// Handle SQS events.
async fn event_handler(_: LambdaEvent<()>) -> Result<(), Error> {
    let sqs = SQS::with_default_client().await?;
    let events = sqs.receive().await?;

    let s3 = S3::with_defaults().await?;
    let events = s3.update_events(events).await?;

    let mut ingester = Ingester::new_with_defaults().await?;

    ingester.ingest_events(events.into()).await?;

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
