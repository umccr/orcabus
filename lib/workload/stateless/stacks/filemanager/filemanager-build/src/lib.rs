use clap::Parser;
use std::env::var;
use std::path::{Path, PathBuf};

use error::Result;

use crate::error::Error;
use crate::error::ErrorKind::LoadingEnvironment;

pub mod error;
pub mod gen_entities;
pub mod gen_openapi;

/// Run the filemanager-build tool to generate sea-orm entities. This always generates entities
/// if a database url is defined, otherwise it skips generating entities if `--skip-if-no-database`
/// is used, or errors if it is not.
#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
pub struct Config {
    /// Skip generating if no database URL is set. This allows assuming that any
    /// checked-in code is up-to-date with the database and proceeding with the build.
    #[arg(short, long, default_value_t = false, env)]
    pub(crate) skip_if_no_database: bool,
    /// The database URL to use for generating entities.
    #[arg(short, long, default_value = "", env)]
    pub(crate) database_url: String,
    /// The output directory.
    #[arg(short, long, env)]
    pub(crate) out_dir: PathBuf,
}

impl Config {
    /// Load environment variables into a `Config` struct.
    #[track_caller]
    pub fn load() -> Result<Self> {
        let args = Config::parse();

        if !args.skip_if_no_database && args.database_url.is_empty() {
            return Err(LoadingEnvironment(
                "Missing database URL and not skipping entity generation".to_string(),
            )
            .into());
        }

        Ok(args)
    }

    /// Get whether to skip the generation if the database URL is empty.
    pub fn skip_if_no_database(&self) -> bool {
        self.skip_if_no_database && self.database_url.is_empty()
    }

    /// Get the database url.
    pub fn database_url(&self) -> &str {
        &self.database_url
    }

    /// Get the out dir.
    pub fn out_dir(&self) -> &Path {
        &self.out_dir
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
