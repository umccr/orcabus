use aws_lambda_events::sqs::SqsEvent;
use lambda_runtime::{run, service_fn, Error, LambdaEvent};

use filemanager::clients::aws::s3::Client;
use filemanager::database::Client as DbClient;
use filemanager::env::Config;
use filemanager::handlers::aws::{create_database_pool, ingest_event, update_credentials};
use filemanager::handlers::init_tracing;

#[tokio::main]
async fn main() -> Result<(), Error> {
    init_tracing();

    let config = &Config::load()?;
    let options = &create_database_pool(config).await?;
    run(service_fn(|event: LambdaEvent<SqsEvent>| async move {
        update_credentials(options, config).await?;

        ingest_event(
            event.payload,
            Client::with_defaults().await,
            DbClient::new(options.clone()),
            config,
        )
        .await?;

        Ok::<(), Error>(())
    }))
    .await
}
