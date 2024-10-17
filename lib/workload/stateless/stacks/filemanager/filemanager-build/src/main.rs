use filemanager_build::gen_entities::generate_entities;
use filemanager_build::gen_openapi::generate_openapi;
use filemanager_build::gen_schemas::write_schemas;
use filemanager_build::{Config, SubCommands};
use miette::Result;

#[tokio::main]
async fn main() -> Result<()> {
    let _ = dotenvy::dotenv();
    let config = Config::load()?;

    match config.into_inner() {
        SubCommands::Entities {
            skip_if_no_database,
            database_url,
            out_dir,
        } => {
            if !skip_if_no_database {
                generate_entities(&out_dir, &database_url, false).await?;
                generate_openapi(&out_dir).await?;
            } else {
                println!("Skipping entity generation as no database url is defined, nothing to do.")
            }
        }
        SubCommands::Schemas { out_dir, .. } => {
            write_schemas(&out_dir).await?;
        }
    }

    Ok(())
}
