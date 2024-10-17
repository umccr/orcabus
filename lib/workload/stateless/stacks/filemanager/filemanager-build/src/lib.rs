use clap::{Parser, Subcommand};
use std::env::var;
use std::path::{Path, PathBuf};

use error::Result;

use crate::error::Error;
use crate::error::ErrorKind::LoadingEnvironment;

pub mod error;
pub mod gen_entities;
pub mod gen_openapi;
pub mod gen_schemas;
pub mod types;

/// Run the filemanager-build tool to generate sea-orm entities or generate JSON schemas. This always generates entities
/// if a database url is defined, otherwise it skips generating entities if `--skip-if-no-database`
/// is used, or errors if it is not.
#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
pub struct Config {
    /// The filemanager-build subcommands.
    #[command(subcommand)]
    pub(crate) sub_commands: SubCommands,
}

impl Config {
    /// Get the subcommands.
    pub fn into_inner(self) -> SubCommands {
        self.sub_commands
    }
}

/// The filemanager-build subcommands.
#[derive(Subcommand, Debug, Clone)]
pub enum SubCommands {
    /// Generate sea-orm entities. This always generates entities if a database url is defined,
    /// otherwise it skips generating entities if `--skip-if-no-database` is used, or errors if it
    /// is not.
    Entities {
        /// Skip generating if no database URL is set. This allows assuming that any
        /// checked-in code is up-to-date with the database and proceeding with the build.
        #[arg(short, long, default_value_t = false, env)]
        skip_if_no_database: bool,
        /// The database URL to use for generating entities.
        #[arg(short, long, default_value = "", env)]
        database_url: String,
        /// The output directory.
        #[arg(short, long, env)]
        out_dir: PathBuf,
    },
    /// Generate the JSON schemas that filemanager can consume.
    Schemas {
        /// The output directory.
        #[arg(short, long, env)]
        out_dir: PathBuf,
        /// Whether to generate schema examples.
        #[arg(short, long, default_value_t = true, env)]
        examples: bool,
    },
}

impl Config {
    /// Load environment variables into a `Config` struct.
    #[track_caller]
    pub fn load() -> Result<Self> {
        let args = Config::parse();

        if let SubCommands::Entities {
            skip_if_no_database,
            database_url,
            ..
        } = &args.sub_commands
        {
            if !skip_if_no_database && database_url.is_empty() {
                return Err(LoadingEnvironment(
                    "Missing database URL and not skipping entity generation".to_string(),
                )
                .into());
            }
        }

        Ok(args)
    }
}

/// Get the path of the workspace.
pub fn workspace_path() -> Option<PathBuf> {
    // This is separate to the `Config` struct to avoid a stack overflow from infinite
    // recursion when rendering an error, which also depends on the `CARGO_MANIFEST_DIR`.
    var("CARGO_MANIFEST_DIR")
        .map(|dir| Path::new(&dir).join(".."))
        .ok()
}

/// Print messages to trigger a rebuild if the code changes.
pub fn rebuild_if_changed() -> Result<()> {
    let root_dir = workspace_path()
        .ok_or_else(|| Error::from(LoadingEnvironment("`CARGO_MANIFEST_DIR`".to_string())))?;

    let database_dir = root_dir.join("database");
    println!("cargo:rerun-if-changed={}", database_dir.display());

    Ok(())
}
