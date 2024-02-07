use lambda_http::Error;
use lambda_runtime::{run, service_fn, LambdaEvent};
use tracing_subscriber::layer::SubscriberExt;
use tracing_subscriber::util::SubscriberInitExt;
use tracing_subscriber::{fmt, EnvFilter};

use filemanager::clients::aws::s3::Client as S3Client;
use filemanager::clients::aws::sqs::Client as SQSClient;
use filemanager::handlers::aws::receive_and_ingest;

#[tokio::main]
async fn main() -> Result<(), Error> {
    let env_filter = EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info"));

    tracing_subscriber::registry()
        .with(fmt::layer().json().without_time())
        .with(env_filter)
        .init();

    run(service_fn(|_: LambdaEvent<()>| async move {
        receive_and_ingest(
            S3Client::with_defaults().await,
            SQSClient::with_defaults().await,
            None::<String>,
            None,
        )
        .await?;

        Ok::<(), Error>(())
    }))
    .await
}
