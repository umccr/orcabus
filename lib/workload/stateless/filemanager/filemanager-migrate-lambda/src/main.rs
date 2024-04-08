use std::collections::HashMap;

use lambda_runtime::{run, service_fn, Error, LambdaEvent};
use tracing_subscriber::layer::SubscriberExt;
use tracing_subscriber::util::SubscriberInitExt;
use tracing_subscriber::{fmt, EnvFilter};

use filemanager::database::aws::migration::Migration;
use filemanager::database::Client as DbClient;
use filemanager::database::Migrate;
use filemanager::handlers::aws::{create_database_pool, update_credentials};

#[tokio::main]
async fn main() -> Result<(), Error> {
    let env_filter = EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info"));

    tracing_subscriber::registry()
        .with(fmt::layer().json().without_time())
        .with(env_filter)
        .init();

    let options = &create_database_pool().await?;
    run(service_fn(
        |_: LambdaEvent<HashMap<String, String>>| async move {
            update_credentials(options).await?;

            Ok::<(), Error>(
                Migration::new(DbClient::from_ref(options))
                    .migrate()
                    .await?,
            )
        },
    ))
    .await
}
