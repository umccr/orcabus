use aws_lambda_events::sqs::SqsEvent;
use lambda_runtime::{run, service_fn, Error, LambdaEvent};
use tracing::trace;
use tracing_subscriber::layer::SubscriberExt;
use tracing_subscriber::util::SubscriberInitExt;
use tracing_subscriber::{fmt, EnvFilter};

use filemanager::database::s3::ingester::Ingester;
use filemanager::database::Ingest;
use filemanager::events::s3::collect::Collecter;
use filemanager::events::s3::FlatS3EventMessages;
use filemanager::events::Collect;

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

    let events = Collecter::with_defaults(events).await?.collect().await?;

    trace!("ingesting events: {:?}", events);

    let mut ingester = Ingester::new_with_defaults().await?;
    trace!("ingester: {:?}", ingester);
    ingester.ingest(events).await?;

    Ok(())
}

#[tokio::main]
async fn main() -> Result<(), Error> {
    let env_filter = EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info"));

    tracing_subscriber::registry()
        .with(fmt::layer().json().without_time())
        .with(env_filter)
        .init();

    run(service_fn(event_handler)).await
}
