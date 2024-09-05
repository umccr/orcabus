use filemanager_build::gen_entities::generate_entities;
use filemanager_build::gen_openapi::generate_openapi;
use filemanager_build::Config;
use miette::Result;

#[tokio::main]
async fn main() -> Result<()> {
    let _ = dotenvy::dotenv();
    let config = Config::load()?;

    if !config.skip_if_no_database() {
        generate_entities(config.out_dir(), config.database_url(), false).await?;
        generate_openapi(config.out_dir()).await?;
    } else {
        println!("Skipping entity generation as no database url is defined, nothing to do.")
    }

    Ok(())
}
