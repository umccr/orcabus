//! This module is responsible for generating sea-orm entities based on the current development
//! database schema.
//!

use crate::error::ErrorKind::EntityGeneration;
use crate::error::{Error, Result};
use crate::Config;
use clap_builder::Parser;
use quote::quote;
use sea_orm_cli::{run_generate_command, Cli, Commands};
use std::ffi::OsStr;
use std::fs::write;

pub async fn generate_entities() -> Result<()> {
    let config = Config::load()?;

    let out_dir = config.out_dir;
    let command: &[&_] = &[
        "sea-orm-cli",
        "generate",
        "entity",
        "--with-serde",
        "both",
        "-u",
        &config.database_url,
        "-o",
    ]
    .map(OsStr::new);

    let cli = Cli::parse_from([command, &[out_dir.as_os_str()]].concat());
    if let Commands::Generate { command } = cli.command {
        run_generate_command(command, true)
            .await
            .map_err(|err| Error::from(EntityGeneration(err.to_string())))?;
    } else {
        panic!("command must be generate");
    }

    let path = out_dir.join("mod.rs");
    let path = path.to_string_lossy();
    let generated = quote!(
        // Auto-generated by the filemanager build script.
        #[path = #path]
        pub mod entities;
    );

    write(out_dir.join("entities.rs"), generated.to_string())?;

    Ok(())
}
