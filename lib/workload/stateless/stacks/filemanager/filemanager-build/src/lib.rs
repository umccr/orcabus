use std::env::var;
use std::path::Path;
use error::Result;
use crate::error::Error::MissingEnvironment;

pub mod error;
// pub mod entities;

/// Print messages to trigger a rebuild if the code changes.
pub fn rebuild_if_changed() -> Result<()> {
    let root_dir = Path::new(&var("CARGO_MANIFEST_DIR").map_err(|err| MissingEnvironment(err.to_string()))?).join("..");
    
    let database_dir = root_dir.join("database");
    println!("cargo:rerun-if-changed={}", database_dir.display());

    Ok(())
}