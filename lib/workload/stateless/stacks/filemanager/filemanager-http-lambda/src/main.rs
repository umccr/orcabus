use lambda_http::Error;
use lambda_runtime::{run, service_fn, LambdaEvent};

use filemanager::clients::aws::s3::Client as S3Client;
use filemanager::clients::aws::sqs::Client as SQSClient;
use filemanager::database::Client as DbClient;
use filemanager::handlers::aws::{create_database_pool, receive_and_ingest, update_credentials};
use filemanager::handlers::init_tracing;

#[tokio::main]
async fn main() -> Result<(), Error> {
    init_tracing();

    let options = &create_database_pool().await?;
    run(service_fn(|_: LambdaEvent<()>| async move {
        update_credentials(options).await?;

        receive_and_ingest(
            S3Client::with_defaults().await,
            SQSClient::with_defaults().await,
            None::<String>,
            DbClient::from_ref(options),
        )
        .await?;

        Ok::<(), Error>(())
    }))
    .await
}
