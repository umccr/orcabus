//! This module is responsible for generating sea-orm entities based on the current development
//! database schema.
//!

use crate::error::ErrorKind::EntityGeneration;
use crate::error::{Error, Result};
use crate::Config;
use clap_builder::Parser;
use sea_orm_cli::{run_generate_command, Cli, Commands};
use std::ffi::OsStr;
use std::fs::{File, read_dir, write};
use std::io::read_to_string;
use temp_dir::TempDir;

pub async fn generate_entities() -> Result<()> {
    let config = Config::load()?;

    let dir = TempDir::new()?;
    let command: &[&_] = &[
        "sea-orm-cli",
        "generate",
        "entity",
        "-u",
        &config.database_url,
        "-o",
    ]
    .map(OsStr::new);

    let cli = Cli::parse_from([command, &[dir.path().as_os_str()]].concat());
    if let Commands::Generate { command } = cli.command {
        run_generate_command(command, true)
            .await
            .map_err(|err| Error::from(EntityGeneration(err.to_string())))?;
    } else {
        panic!("command must be generate");
    }

    let mut sources = vec![];
    for path in  read_dir(dir.path())? {
        let entry = path?;
        let source = read_to_string(File::open(entry.path())?)?;
        sources.push(source);
    }

    write(config.out_dir.join("generated.rs"), format!("pub mod generated {{\n {} \n}}", sources.join("\n")))?;
    
    Ok(())
}
