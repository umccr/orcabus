//! This module is responsible for generating sea-orm entities based on the current development
//! database schema.
//!

use crate::error::ErrorKind::EntityGeneration;
use crate::error::Result;
use crate::Config;
use clap_builder::Parser;
use sea_orm_cli::{run_generate_command, Cli, Commands};
use std::ffi::OsStr;

pub async fn generate_entities() -> Result<()> {
    let config = Config::load()?;

    let command: &[&_] = &[
        "sea-orm-cli",
        "generate",
        "entity",
        "-u",
        &config.database_url,
        "-o",
    ]
    .map(OsStr::new);
    let cli = Cli::parse_from([command, &[config.out_dir.as_os_str()]].concat());
    if let Commands::Generate { command } = cli.command {
        run_generate_command(command, true)
            .await
            .map_err(|err| EntityGeneration(err.to_string()).into())
    } else {
        panic!("command must be generate");
    }
}
