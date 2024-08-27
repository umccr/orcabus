use miette::Result;

use filemanager_build::gen_entities::generate_entities;
use filemanager_build::gen_openapi::generate_openapi;
use filemanager_build::rebuild_if_changed;

#[tokio::main]
async fn main() -> Result<()> {
    // Try anyway even if there is no .env file.
    let _ = dotenvy::dotenv();

    generate_entities().await?;
    generate_openapi().await?;

    Ok(rebuild_if_changed()?)
}
