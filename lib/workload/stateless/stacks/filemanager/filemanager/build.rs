use filemanager_build::gen_entities::generate_entities;
use filemanager_build::rebuild_if_changed;
use miette::Result;

#[tokio::main]
async fn main() -> Result<()> {
    // Try anyway even if there is no .env file.
    let _ = dotenvy::dotenv();

    generate_entities().await?;
    Ok(rebuild_if_changed()?)
}
