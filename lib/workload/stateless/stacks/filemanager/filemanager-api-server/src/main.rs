use std::io;
use std::path::PathBuf;
use std::sync::Arc;

use axum::serve;
use clap::{Parser, Subcommand};
use http::Uri;
use sea_orm::ConnectionTrait;
use tokio::fs::File;
use tokio::io::AsyncReadExt;
use tokio::net::TcpListener;
use tracing::{debug, info};

use filemanager::clients::aws::{s3, secrets_manager, sqs};
use filemanager::database::aws::migration::Migration;
use filemanager::database::{Client, Migrate};
use filemanager::env::Config;
use filemanager::error::Error::IoError;
use filemanager::error::Result;
use filemanager::handlers::init_tracing_with_format;
use filemanager::handlers::Format::Pretty;
use filemanager::queries::EntriesBuilder;
use filemanager::routes::openapi::SWAGGER_UI_PATH;
use filemanager::routes::{router, AppState};

/// Run the filemanager API server locally to explore the API.
#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Args {
    /// The address to run the server at.
    #[arg(short, long, default_value = "0.0.0.0:8000", env)]
    api_server_addr: String,
    /// Load an .sql dump into the filemanager database. This executes an unprepared
    /// .sql script from the file specified.
    #[arg(short, long, env)]
    load_sql_file: Option<PathBuf>,
    /// Apply migrations before starting the server.
    #[arg(short, long, default_value_t = false, env)]
    migrate: bool,
    /// Mock testing data for the API to use. Records are generated incrementally
    /// with integers as buckets and keys.
    #[command(subcommand)]
    mock_data: Option<MockData>,
}

/// Mock data into the filemanager database.
#[derive(Subcommand, Debug)]
pub enum MockData {
    /// Mock data into the filemanager database. Note that this should only be run once on the same
    /// postgres database to avoid duplicate key errors.
    Mock {
        /// The number of records to generate.
        #[arg(short, long, default_value_t = 1000, env)]
        n_records: usize,
        /// The ratio of buckets to use when generating records. A higher number here means
        /// that less buckets will be generated.
        #[arg(short, long, default_value_t = 100, env)]
        bucket_divisor: usize,
        /// The ratio of keys to use when generating records. A higher number here means
        /// that less keys will be generated.
        #[arg(short, long, default_value_t = 10, env)]
        key_divisor: usize,
        /// Whether to shuffle the generated records to simulate out of order events.
        #[arg(short, long, default_value_t = true, env)]
        shuffle: bool,
    },
}

#[tokio::main]
async fn main() -> Result<()> {
    let _ = dotenvy::dotenv();
    let args = Args::parse();

    init_tracing_with_format(Pretty);

    let config = Arc::new(Config::load()?);
    debug!(?config, "running with config");

    let client = Client::from_config(&config).await?;
    let state = AppState::new(
        client.clone(),
        config.clone(),
        Arc::new(s3::Client::with_defaults().await),
        Arc::new(sqs::Client::with_defaults().await),
        Arc::new(secrets_manager::Client::with_defaults().await?),
        // For now, the local server is always non-TLS.
        false,
    );

    if let Some(load) = args.load_sql_file {
        info!(
            from = load.to_string_lossy().as_ref(),
            "loading .sql script"
        );

        let mut script = String::new();
        File::open(load).await?.read_to_string(&mut script).await?;

        state
            .database_client()
            .connection_ref()
            .execute_unprepared(&script)
            .await?;
    }

    if let Some(MockData::Mock {
        n_records,
        bucket_divisor,
        key_divisor,
        shuffle,
    }) = args.mock_data
    {
        info!("generating mock database records");

        EntriesBuilder::default()
            .with_n(n_records)
            .with_bucket_divisor(bucket_divisor)
            .with_key_divisor(key_divisor)
            .with_shuffle(shuffle)
            .build(state.database_client())
            .await?;
    }

    if args.migrate {
        Migration::new(client).migrate().await?;
    }

    let app = router(state)?;
    let listener = TcpListener::bind(args.api_server_addr).await?;

    let local_addr = listener.local_addr()?;
    info!("listening on {}", listener.local_addr()?);

    let docs = Uri::builder()
        .scheme("http")
        .authority(local_addr.to_string())
        .path_and_query(SWAGGER_UI_PATH)
        .build()
        .map_err(|err| IoError(io::Error::other(err)))?;

    info!("OpenAPI docs at {}", docs);

    Ok(serve(listener, app).await?)
}
