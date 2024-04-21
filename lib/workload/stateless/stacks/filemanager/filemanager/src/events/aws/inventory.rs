//! Handles S3 Inventory reports and converts them to events that can be ingested.
//!

use std::result;
use aws_sdk_s3::types::InventoryFormat;
use crate::events::aws::message::EventType::Created;
use crate::events::aws::{FlatS3EventMessage, FlatS3EventMessages, StorageClass};
use crate::uuid::UuidGenerator;
use chrono::{DateTime, Utc};
use csv::{Reader, ReaderBuilder, StringRecord};
use futures::future::join_all;
use serde::{Deserialize, Serialize};
use serde_with::{serde_as, DisplayFromStr};
use crate::clients::aws::s3::Client;
use crate::error::Error::S3InventoryError;
use crate::error::{Error, Result};

/// Represents an S3 inventory including associated inventory fetching and parsing logic.
#[derive(Debug)]
pub struct Inventory {
    client: Client,
}

impl Inventory {
    /// Create a new inventory.
    pub fn new(client: Client) -> Self {
        Self { client }
    }

    /// Create a new inventory with a default s3 client.
    pub async fn with_defaults() -> Self {
        Self::new(Client::with_defaults().await)
    }
    
    /// Parse a manifest into records.
    pub async fn parse_manifest(&self, manifest: Manifest) -> Result<Vec<Record>> {
        match manifest.file_format {
            InventoryFormat::Csv => {
                // todo, fix to handle proper arns including accounts/regions.
                let bucket = manifest.destination_bucket.strip_prefix("arn:aws:s3:::").unwrap_or_else(|| &manifest.destination_bucket);
                let inventories: Vec<Record> = join_all(manifest.files.iter().map(|file| async {
                    let inventory = self.client
                        .get_object(&file.key, bucket)
                        .await.map_err(|err| S3InventoryError(format!("getting inventory: {}", err)))?;

                    let inventory = inventory.body.collect().await.map_err(|_| S3InventoryError("collecting inventory bytes".to_string()))?.to_vec();

                    let mut header_record = StringRecord::new();
                    Reader::from_reader(manifest.file_schema.as_bytes()).read_record(&mut header_record)?;

                    let mut csv = ReaderBuilder::new().has_headers(false).from_reader(inventory.as_slice());
                    csv.set_headers(header_record);

                    let records: result::Result<Vec<Record>, csv::Error> = csv.deserialize::<Record>().collect();
                    Ok::<_, Error>(records?)
                })).await.into_iter().collect::<Result<Vec<Vec<Record>>>>()?.into_iter().flatten().collect();

                Ok(inventories)
            },
            _ => Err(S3InventoryError("unsupported format".to_string()))
        }
    }
}

impl From<csv::Error> for Error {
    fn from(error: csv::Error) -> Self {
        S3InventoryError(error.to_string())
    }
}

/// An S3 inventory record.
#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "PascalCase")]
pub struct Record {
    bucket: String,
    key: String,
    version_id: Option<String>,
    size: Option<i64>,
    last_modified_date: Option<DateTime<Utc>>,
    e_tag: Option<String>,
    storage_class: Option<StorageClass>,
}

/// The manifest format for an inventory.
#[serde_as]
#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Manifest {
    destination_bucket: String,
    #[serde_as(as = "DisplayFromStr")]
    file_format: InventoryFormat,
    file_schema: String,
    files: Vec<File>
}

/// The files inside the manifest.
#[derive(Debug, Serialize, Deserialize)]
pub struct File {
    key: String,
    #[serde(rename = "MD5checksum")]
    md5_checksum: String,
}

impl From<Vec<Record>> for FlatS3EventMessages {
    fn from(records: Vec<Record>) -> Self {
        Self(records.into_iter().map(|record| record.into()).collect())
    }
}

impl From<Record> for FlatS3EventMessages {
    fn from(record: Record) -> Self {
        Self(vec![record.into()])
    }
}

impl From<Record> for FlatS3EventMessage {
    fn from(record: Record) -> Self {
        let Record {
            bucket,
            key,
            version_id,
            size,
            last_modified_date,
            e_tag,
            storage_class,
        } = record;

        Self {
            s3_object_id: UuidGenerator::generate(),
            // We don't know when this object was created so there is no event time.
            event_time: None,
            bucket,
            key,
            size,
            e_tag,
            // Set this to the empty string so that any deleted events after this can bind to this
            // created event.
            sequencer: Some("".to_string()),
            version_id: version_id.unwrap_or_else(FlatS3EventMessage::default_version_id),
            storage_class,
            last_modified_date,
            sha256: None,
            // Anything in an inventory report is always a created event.
            event_type: Created,
            number_reordered: 0,
            number_duplicate_events: 0,
        }
    }
}
