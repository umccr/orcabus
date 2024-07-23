use axum::serve;
use clap::{Parser, Subcommand};
use filemanager::database::Client;
use filemanager::env::Config;
use filemanager::error::Error::IoError;
use filemanager::error::Result;
use filemanager::handlers::init_tracing_with_format;
use filemanager::handlers::Format::Pretty;
use filemanager::queries::EntriesBuilder;
use filemanager::routes::{router, AppState};
use http::Uri;
use sea_orm::ConnectionTrait;
use std::io;
use std::path::PathBuf;
use std::sync::Arc;
use tokio::fs::File;
use tokio::io::AsyncReadExt;
use tokio::net::TcpListener;
use tracing::{debug, info};

/// Run the filemanager API server locally to explore the API.
#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Args {
    /// The address to run the server at.
    #[arg(short, long, default_value = "localhost:8080")]
    api_server_addr: String,
    /// Load an .sql dump into the filemanager database. This executes an unprepared
    /// .sql script from the file specified.
    #[arg(short, long)]
    load_sql_file: Option<PathBuf>,
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
        #[arg(short, long, default_value_t = 1000)]
        n_records: usize,
        /// The ratio of buckets to use when generating records. A higher number here means
        /// that less buckets will be generated.
        #[arg(short, long, default_value_t = 100)]
        bucket_divisor: usize,
        /// The ratio of keys to use when generating records. A higher number here means
        /// that less keys will be generated.
        #[arg(short, long, default_value_t = 10)]
        key_divisor: usize,
        /// Whether to shuffle the generated records to simulate out of order events.
        #[arg(short, long, default_value_t = true)]
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
    let state = AppState::new(client, config.clone());

    if let Some(load) = args.load_sql_file {
        info!(
            from = load.to_string_lossy().as_ref(),
            "loading .sql script"
        );

        let mut script = String::new();
        File::open(load).await?.read_to_string(&mut script).await?;

        state
            .client()
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
            .build(state.client())
            .await;
    }

    let app = router(state);
    let listener = TcpListener::bind(args.api_server_addr).await?;

    let local_addr = listener.local_addr()?;
    info!("listening on {}", listener.local_addr()?);

    let docs = Uri::builder()
        .scheme("http")
        .authority(local_addr.to_string())
        .path_and_query("/swagger_ui")
        .build()
        .map_err(|err| IoError(io::Error::other(err)))?;

    info!("OpenAPI docs at {}", docs);

    Ok(serve(listener, app).await?)
}
