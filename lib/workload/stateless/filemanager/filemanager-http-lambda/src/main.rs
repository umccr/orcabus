use filemanager::database::s3::ingester::Ingester;
use filemanager::events::Collect;
use filemanager::events::s3::sqs::SQS;
use lambda_http::Error;
use lambda_runtime::{run, service_fn, LambdaEvent};
use tracing_subscriber::{EnvFilter, fmt};
use tracing_subscriber::layer::SubscriberExt;
use tracing_subscriber::util::SubscriberInitExt;
use filemanager::database::Ingest;
use filemanager::events::s3::collect::Collecter;

/// Handle SQS events.
async fn event_handler(_: LambdaEvent<()>) -> Result<(), Error> {
    let sqs = SQS::with_default_client().await?;
    let events = sqs.receive().await?;

    let events = Collecter::with_defaults(events).await?.collect().await?;

    let mut ingester = Ingester::new_with_defaults().await?;

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
