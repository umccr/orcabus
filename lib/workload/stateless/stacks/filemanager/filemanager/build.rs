use filemanager_build::rebuild_if_changed;
use miette::Result;

fn main() -> Result<()> {
    Ok(rebuild_if_changed()?)
}
