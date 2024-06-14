use filemanager_build::entities::generate_entities;
use filemanager_build::rebuild_if_changed;
use miette::Result;

#[tokio::main]
async fn main() -> Result<()> {
    generate_entities().await?;
    Ok(rebuild_if_changed()?)
}
