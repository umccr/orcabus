use crate::error::Error;
use crate::error::ErrorKind::LoadingEnvironment;
use envy::from_env;
use error::Result;
use serde::Deserialize;
use std::env::var;
use std::path::{Path, PathBuf};

pub mod entities;
pub mod error;

/// Configuration environment variables for the build process.
#[derive(Debug, Deserialize)]
pub struct Config {
    database_url: String,
    out_dir: PathBuf,
}

impl Config {
    /// Load environment variables into a `Config` struct.
    #[track_caller]
    pub fn load() -> Result<Self> {
        Ok(from_env::<Config>()?)
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
