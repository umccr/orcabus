//! Logic for AWS EventBridge schema for filemanager.
//!

use crate::error::ErrorKind::SchemaGeneration;
use crate::error::Result;
use crate::types::FileStateChange;
use crate::types::{Detail, FileStateChangeType, StorageClass, Transition};
use chrono::Utc;
use schemars::gen::{SchemaGenerator, SchemaSettings};
use serde::Serialize;
use serde_json::to_string_pretty;
use std::fs::File;
use std::io::Write;
use std::path::Path;
use tokio::fs::create_dir_all;
use uuid::Uuid;

/// Write the schema and examples to the out directory.
pub async fn write_schemas(out_dir: &Path) -> Result<()> {
    create_dir_all(out_dir.join("example")).await?;

    let mut example_one = File::create(out_dir.join("example/FSC__example1.json"))?;
    writeln!(example_one, "{}", generate_example_one().await?)?;

    let mut example_two = File::create(out_dir.join("example/FSC__example2.json"))?;
    writeln!(example_two, "{}", generate_example_two().await?)?;

    let mut schema = File::create(out_dir.join("FileStateChange.schema.json"))?;
    writeln!(schema, "{}", generate_file_schema().await?)?;

    Ok(())
}

/// Generate the JSON schemas.
pub async fn generate_file_schema() -> Result<String> {
    let mut settings = SchemaSettings::default();
    settings.meta_schema = Some("http://json-schema.org/draft-04/schema#".to_string());
    let schema = SchemaGenerator::new(settings).into_root_schema_for::<FileStateChange>();

    to_json_string(&schema).await
}

/// Generate an example schema for an expiration rule.
pub async fn generate_example_one() -> Result<String> {
    let example = FileStateChange {
        detail_type: FileStateChangeType::FileStateChange,
        detail: Detail {
            prefix: None,
            transitions: None,
            expiration: Some(30),
            object_size_less_than: None,
            object_size_greater_than: Some(1024),
            keep_on_move: true,
        },
        source: "orcabus.filemanager".to_string(),
        version: Some("0".to_string()),
        id: Some(Uuid::now_v7()),
        account: Some("123456789012".to_string()),
        time: Some(Utc::now()),
        region: Some("ap-southeast-2".to_string()),
        resources: Some(vec![]),
    };

    to_json_string(&example).await
}

/// Generate an example schema for transition rules and an expiration rule.
pub async fn generate_example_two() -> Result<String> {
    let example = FileStateChange {
        detail_type: FileStateChangeType::FileStateChange,
        detail: Detail {
            prefix: Some("key_prefix/".to_string()),
            transitions: Some(vec![
                Transition {
                    storage_class: StorageClass::StandardIa,
                    days: 30,
                },
                Transition {
                    storage_class: StorageClass::Glacier,
                    days: 90,
                },
            ]),
            expiration: Some(365),
            object_size_less_than: Some(1024),
            object_size_greater_than: None,
            keep_on_move: false,
        },
        source: "orcabus.filemanager".to_string(),
        version: Some("0".to_string()),
        id: Some(Uuid::now_v7()),
        account: Some("123456789012".to_string()),
        time: Some(Utc::now()),
        region: Some("ap-southeast-2".to_string()),
        resources: Some(vec![]),
    };

    to_json_string(&example).await
}

async fn to_json_string<T: ?Sized + Serialize>(value: &T) -> Result<String> {
    Ok(to_string_pretty(value).map_err(|err| SchemaGeneration(err.to_string()))?)
}

#[cfg(test)]
mod tests {
    use super::*;
    use jsonschema::draft4::is_valid;
    use serde_json::from_str;

    #[tokio::test]
    async fn test_schemas() {
        let schema = from_str(&generate_file_schema().await.unwrap()).unwrap();

        let example_one = from_str(&generate_example_one().await.unwrap()).unwrap();
        assert!(is_valid(&schema, &example_one));

        let example_two = from_str(&generate_example_two().await.unwrap()).unwrap();
        assert!(is_valid(&schema, &example_two));
    }
}
