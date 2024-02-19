use aws_lambda_events::sqs::SqsEvent;
use lambda_runtime::{run, service_fn, Error, LambdaEvent};
use tracing_subscriber::layer::SubscriberExt;
use tracing_subscriber::util::SubscriberInitExt;
use tracing_subscriber::{fmt, EnvFilter};

use filemanager::clients::aws::s3::Client;
use filemanager::handlers::aws::ingest_event;

#[tokio::main]
async fn main() -> Result<(), Error> {
    let env_filter = EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info"));

    tracing_subscriber::registry()
        .with(fmt::layer().json().without_time())
        .with(env_filter)
        .init();

    run(service_fn(|event: LambdaEvent<SqsEvent>| async move {
        ingest_event(event.payload, Client::with_defaults().await, None).await?;

        Ok::<(), Error>(())
    }))
    .await
}
