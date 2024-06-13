use crate::error::ErrorKind::MissingEnvironment;
use error::Result;
use std::env::var;
use std::path::{Path, PathBuf};

// pub mod entities;
pub mod error;

/// Get the path of the workspace.
pub fn workspace_path() -> Result<PathBuf> {
    var("CARGO_MANIFEST_DIR")
        .map(|path| Path::new(&path).join(".."))
        .map_err(|err| MissingEnvironment(err.to_string()).into())
}

/// Print messages to trigger a rebuild if the code changes.
pub fn rebuild_if_changed() -> Result<()> {
    let root_dir = workspace_path()?;

    let database_dir = root_dir.join("database");
    println!("cargo:rerun-if-changed={}", database_dir.display());

    Ok(())
}
