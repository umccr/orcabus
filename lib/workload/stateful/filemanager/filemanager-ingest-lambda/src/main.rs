use filemanager::clients::aws::s3::Client;
use lambda_runtime::{run, service_fn, Error};
use tracing_subscriber::layer::SubscriberExt;
use tracing_subscriber::util::SubscriberInitExt;
use tracing_subscriber::{fmt, EnvFilter};

use filemanager::handlers::aws::ingest_event;

#[tokio::main]
async fn main() -> Result<(), Error> {
    let env_filter = EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info"));

    tracing_subscriber::registry()
        .with(fmt::layer().json().without_time())
        .with(env_filter)
        .init();

    run(service_fn(|event| async move {
        ingest_event(event, Client::with_defaults().await).await
    }))
    .await
}
