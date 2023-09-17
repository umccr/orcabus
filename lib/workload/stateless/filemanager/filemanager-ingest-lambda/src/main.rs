use aws_lambda_events::event::sqs::SqsEventObj;
use aws_lambda_events::sqs::SqsEvent;
use lambda_runtime::{run, service_fn, Error, LambdaEvent};
use serde::{Deserialize, Serialize};
use filemanager::database::s3::ingester::Ingester;
use filemanager::events::s3::{Events, FlatS3EventMessage, FlatS3EventMessages};
use filemanager::events::s3::s3::S3;

/// This is the main body for the function.
/// You can use the data sent into SQS here.
async fn function_handler(event: LambdaEvent<SqsEvent>) -> Result<(), Error> {
    let events = event.payload.records.into_iter().filter_map(|event| {
        event.body.map(|body| {
            let body: FlatS3EventMessages = serde_json::from_str(&body).unwrap();
            body
        })
    }).collect::<Vec<FlatS3EventMessages>>();

    let e = events.into_iter().next().unwrap().body;
    let s3 = S3::with_defaults().await?;
    let e = s3.update_events(e).await?;

    let e = Events::from(e);

    let mut ingester = Ingester::new_with_defaults().await?;

    ingester.ingest_events(e).await?;

    Ok(())
}

#[tokio::main]
async fn main() -> Result<(), Error> {
    // required to enable CloudWatch error logging by the runtime
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        // disable printing the name of the module in every log line.
        .with_target(false)
        // disabling time is handy because CloudWatch will add the ingestion time.
        .without_time()
        .init();

    run(service_fn(function_handler)).await
}
