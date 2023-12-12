use lambda_http::Error;
use lambda_runtime::{run, service_fn, LambdaEvent};
use tracing_subscriber::layer::SubscriberExt;
use tracing_subscriber::util::SubscriberInitExt;
use tracing_subscriber::{fmt, EnvFilter};

use filemanager::database::s3::ingester::Ingester;
use filemanager::database::Ingest;
use filemanager::events::s3::collector_builder::CollectorBuilder;
use filemanager::events::Collect;

/// Handle SQS events by manually calling the SQS receive function. This is meant
/// to be run through something like API gateway to manually invoke ingestion.
async fn event_handler(_: LambdaEvent<()>) -> Result<(), Error> {
    let events = CollectorBuilder::default()
        .build_receive()
        .await?
        .collect()
        .await?;

    let mut ingester = Ingester::default().await?;

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
