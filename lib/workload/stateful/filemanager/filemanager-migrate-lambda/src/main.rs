use filemanager::database::aws::migration::Migration;
use filemanager::database::Migrate;
use lambda_runtime::{run, service_fn, Error, LambdaEvent};
use tracing_subscriber::layer::SubscriberExt;
use tracing_subscriber::util::SubscriberInitExt;
use tracing_subscriber::{fmt, EnvFilter};

#[tokio::main]
async fn main() -> Result<(), Error> {
    let env_filter = EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info"));

    tracing_subscriber::registry()
        .with(fmt::layer().json().without_time())
        .with(env_filter)
        .init();

    run(service_fn(|_: LambdaEvent<()>| async move {
        Migration::with_defaults().await?.migrate().await
    }))
    .await
}
