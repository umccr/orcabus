//! Handles S3 Inventory reports and converts them to events that can be ingested.
//!

#[double]
use crate::clients::aws::s3::Client;
use crate::error::Error::S3InventoryError;
use crate::error::{Error, Result};
use crate::events::aws::message::EventType::Created;
use crate::events::aws::{FlatS3EventMessage, FlatS3EventMessages, StorageClass};
use crate::uuid::UuidGenerator;
use aws_arn::known::Service;
use aws_arn::ResourceName;
use aws_sdk_s3::types::InventoryFormat;
use chrono::{DateTime, Utc};
use csv::{ReaderBuilder, StringRecord, Trim};
use flate2::read::MultiGzDecoder;
use futures::future::join_all;
use mockall_double::double;
use serde::{Deserialize, Serialize};
use serde_with::{serde_as, DisplayFromStr};
use std::io::{BufReader, Read};
use std::result;

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

    /// Parse a CSV manifest file into records.
    pub async fn parse_csv(&self, schema: &str, body: &[u8]) -> Result<Vec<Record>> {
        let mut inventory_bytes = vec![];
        MultiGzDecoder::new(BufReader::new(body))
            .read_to_end(&mut inventory_bytes)
            .map_err(|err| S3InventoryError(format!("decompressing CSV: {}", err)))?;

        let mut header_record = StringRecord::new();
        ReaderBuilder::new()
            .trim(Trim::All)
            .has_headers(false)
            .from_reader(schema.as_bytes())
            .read_record(&mut header_record)?;

        let mut csv = ReaderBuilder::new()
            .trim(Trim::All)
            .from_reader(inventory_bytes.as_slice());
        csv.set_headers(header_record);

        Ok(csv.deserialize().collect::<result::Result<_, _>>()?)
    }

    /// Parse a manifest into records.
    pub async fn parse_manifest(&self, manifest: Manifest) -> Result<Vec<Record>> {
        let arn: ResourceName = manifest
            .destination_bucket
            .parse()
            .map_err(|err| S3InventoryError(format!("parsing destination bucket arn: {}", err)))?;

        if arn.service != Service::S3.into() {
            return Err(S3InventoryError(
                "destination bucket ARN is not S3".to_string(),
            ));
        }

        let bucket = arn.resource.to_string();

        let inventories = join_all(manifest.files.iter().map(|file| async {
            let inventory = self
                .client
                .get_object(&file.key, &bucket)
                .await
                .map_err(|err| S3InventoryError(format!("getting inventory: {}", err)))?;
            let body = inventory
                .body
                .collect()
                .await
                .map_err(|_| S3InventoryError("collecting inventory bytes".to_string()))?
                .to_vec();

            if md5::compute(body.as_slice()).0
                != hex::decode(&file.md5_checksum)
                    .map_err(|err| S3InventoryError(format!("decoding hex string: {}", err)))?
                    .as_slice()
            {
                return Err(S3InventoryError(
                    "mismatched MD5 checksums in inventory manifest".to_string(),
                ));
            }

            match manifest.file_format {
                InventoryFormat::Csv => {
                    self.parse_csv(&manifest.file_schema, body.as_slice()).await
                }
                _ => Err(S3InventoryError("unsupported type".to_string())),
            }
        }))
        .await
        .into_iter()
        .collect::<Result<Vec<_>>>()?
        .into_iter()
        .flatten()
        .collect();

        Ok(inventories)
    }
}

impl From<csv::Error> for Error {
    fn from(error: csv::Error) -> Self {
        S3InventoryError(error.to_string())
    }
}

/// An S3 inventory record.
#[derive(Debug, Serialize, Deserialize, PartialEq, Eq)]
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
#[derive(Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct Manifest {
    destination_bucket: String,
    #[serde_as(as = "DisplayFromStr")]
    file_format: InventoryFormat,
    file_schema: String,
    files: Vec<File>,
}

/// The files inside the manifest.
#[derive(Debug, Serialize, Deserialize, PartialEq, Eq)]
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
            // created event, as they are always greater than this event.
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

#[cfg(test)]
mod tests {
    use crate::events::aws::inventory::{File, Manifest};
    use aws_sdk_s3::operation::get_object::GetObjectOutput;
    use aws_sdk_s3::primitives::ByteStream;
    use flate2::read::GzEncoder;
    use mockall::predicate::eq;
    use serde_json::json;

    use super::*;

    #[tokio::test]
    async fn parse_csv_manifest() {
        let data = concat!(
            r#""bucket","key1","0","2024-04-12T06:45:57.000Z","#,
            r#""d41d8cd98f00b204e9800998ecf8427e","STANDARD","false","","SSE-S3","","","","","DISABLED","","#, // pragma: allowlist secret
            r#""acl","#,  // pragma: allowlist secret
            r#""owner""#, // pragma: allowlist secret
            "\n",
            r#""bucket","key2","69897","2024-04-12T06:46:10.000Z","0808c1cdcd44cd5f6fea91a79ad32dc8","#, // pragma: allowlist secret
            r#""STANDARD","false","","SSE-S3","","","","","DISABLED","","#,
            r#""acl","#,
            r#""owner""#
        );

        println!("{:#?}", data);
        let mut bytes = vec![];
        let mut reader = GzEncoder::new(data.as_bytes(), Default::default());
        reader.read_to_end(&mut bytes).unwrap();

        let mut client = Client::default();
        client.expect_get_object()
            .with(eq("Inventory/example-source-bucket/2016-11-06T21-32Z/files/939c6d46-85a9-4ba8-87bd-9db705a579ce.csv.gz"), eq("example-inventory-destination-bucket"))
            .once()
            .returning(move |_, _| Ok(GetObjectOutput::builder().body(
                ByteStream::from(bytes.clone())
            ).build()));

        let inventory = Inventory::new(client);
        let result = inventory.parse_manifest(Manifest {
            destination_bucket: "arn:aws:s3:::example-inventory-destination-bucket".to_string(),
            file_format: InventoryFormat::Csv,
            file_schema: "Bucket, Key, Size, \
                LastModifiedDate, ETag, StorageClass, IsMultipartUploaded, ReplicationStatus, \
                EncryptionStatus, ObjectLockRetainUntilDate, ObjectLockMode, \
                ObjectLockLegalHoldStatus, IntelligentTieringAccessTier, BucketKeyStatus, \
                ChecksumAlgorithm, ObjectAccessControlList, ObjectOwner".to_string(),
            files: vec![File {
                key: "Inventory/example-source-bucket/2016-11-06T21-32Z/files/939c6d46-85a9-4ba8-87bd-9db705a579ce.csv.gz".to_string(),
                md5_checksum: "f11166069f1990abeb9c97ace9cdfabc".to_string(), // pragma: allowlist secret
            }]
        }).await.unwrap();

        assert_eq!(
            result,
            vec![
                Record {
                    bucket: "bucket".to_string(),
                    key: "key1".to_string(),
                    version_id: None,
                    size: Some(0),
                    last_modified_date: Some("2024-04-12T06:45:57.000Z".parse().unwrap()),
                    e_tag: Some("d41d8cd98f00b204e9800998ecf8427e".to_string()),
                    storage_class: Some(StorageClass::Standard),
                },
                Record {
                    bucket: "bucket".to_string(),
                    key: "key2".to_string(),
                    version_id: None,
                    size: Some(69897),
                    last_modified_date: Some("2024-04-12T06:46:10.000Z".parse().unwrap()),
                    e_tag: Some("0808c1cdcd44cd5f6fea91a79ad32dc8".to_string()),
                    storage_class: Some(StorageClass::Standard),
                },
            ]
        );
    }

    #[test]
    fn deserialize_csv_manifest() {
        // Taken from https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-inventory-location.html#storage-inventory-location-manifest
        let manifest = json!({
            "sourceBucket": "example-source-bucket",
            "destinationBucket": "arn:aws:s3:::example-inventory-destination-bucket",
            "version": "2016-11-30",
            "creationTimestamp" : "1514944800000",
            "fileFormat": "CSV",
            "fileSchema": "Bucket, Key, VersionId, IsLatest, IsDeleteMarker, Size, \
                LastModifiedDate, ETag, StorageClass, IsMultipartUploaded, ReplicationStatus, \
                EncryptionStatus, ObjectLockRetainUntilDate, ObjectLockMode, \
                ObjectLockLegalHoldStatus, IntelligentTieringAccessTier, BucketKeyStatus, \
                ChecksumAlgorithm, ObjectAccessControlList, ObjectOwner",
            "files": [{
                "key": "Inventory/example-source-bucket/2016-11-06T21-32Z/files/939c6d46-85a9-4ba8-87bd-9db705a579ce.csv.gz",
                "size": 2147483647,
                "MD5checksum": "f11166069f1990abeb9c97ace9cdfabc" // pragma: allowlist secret
            }]
        });

        let result: Manifest = serde_json::from_value(manifest).unwrap();
        assert_eq!(result, expected_csv_manifest());
    }

    #[test]
    fn deserialize_orc_manifest() {
        // Taken from https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-inventory-location.html#storage-inventory-location-manifest
        let manifest = json!({
            "sourceBucket": "example-source-bucket",
            "destinationBucket": "arn:aws:s3:::example-destination-bucket",
            "version": "2016-11-30",
            "creationTimestamp" : "1514944800000",
            "fileFormat": "ORC",
            "fileSchema": "struct<bucket:string,key:string,version_id:string,is_latest:boolean,\
                is_delete_marker:boolean,size:bigint,last_modified_date:timestamp,e_tag:string,\
                storage_class:string,is_multipart_uploaded:boolean,replication_status:string,\
                encryption_status:string,object_lock_retain_until_date:timestamp,\
                object_lock_mode:string,object_lock_legal_hold_status:string,\
                intelligent_tiering_access_tier:string,bucket_key_status:string,\
                checksum_algorithm:string,object_access_control_list:string,object_owner:string>",
            "files": [{
                "key": "inventory/example-source-bucket/data/d794c570-95bb-4271-9128-26023c8b4900.orc",
                "size": 56291,
                "MD5checksum": "5925f4e78e1695c2d020b9f6eexample"
            }]
        });

        let result: Manifest = serde_json::from_value(manifest).unwrap();
        assert_eq!(result, Manifest {
            destination_bucket: "arn:aws:s3:::example-destination-bucket".to_string(),
            file_format: InventoryFormat::Orc,
            file_schema: "struct<bucket:string,key:string,version_id:string,is_latest:boolean,\
                is_delete_marker:boolean,size:bigint,last_modified_date:timestamp,e_tag:string,\
                storage_class:string,is_multipart_uploaded:boolean,replication_status:string,\
                encryption_status:string,object_lock_retain_until_date:timestamp,\
                object_lock_mode:string,object_lock_legal_hold_status:string,\
                intelligent_tiering_access_tier:string,bucket_key_status:string,\
                checksum_algorithm:string,object_access_control_list:string,object_owner:string>".to_string(),
            files: vec![File {
                key: "inventory/example-source-bucket/data/d794c570-95bb-4271-9128-26023c8b4900.orc".to_string(),
                md5_checksum: "5925f4e78e1695c2d020b9f6eexample".to_string(),
            }],
        });
    }

    #[test]
    fn deserialize_parquet_manifest() {
        // Taken from https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-inventory-location.html#storage-inventory-location-manifest
        let manifest = json!({
            "sourceBucket": "example-source-bucket",
            "destinationBucket": "arn:aws:s3:::example-destination-bucket",
            "version": "2016-11-30",
            "creationTimestamp" : "1514944800000",
            "fileFormat": "Parquet",
            "fileSchema": "message s3.inventory { required binary bucket (UTF8); \
                required binary key (UTF8); optional binary version_id (UTF8); \
                optional boolean is_latest; optional boolean is_delete_marker; \
                optional int64 size; optional int64 last_modified_date (TIMESTAMP_MILLIS); \
                optional binary e_tag (UTF8); optional binary storage_class (UTF8); \
                optional boolean is_multipart_uploaded; optional binary replication_status (UTF8); \
                optional binary encryption_status (UTF8); \
                optional int64 object_lock_retain_until_date (TIMESTAMP_MILLIS); \
                optional binary object_lock_mode (UTF8); \
                optional binary object_lock_legal_hold_status (UTF8); \
                optional binary intelligent_tiering_access_tier (UTF8); \
                optional binary bucket_key_status (UTF8); optional binary checksum_algorithm (UTF8); \
                optional binary object_access_control_list (UTF8); \
                optional binary object_owner (UTF8);}",
            "files": [{
                "key": "inventory/example-source-bucket/data/d754c470-85bb-4255-9218-47023c8b4910.parquet",
                "size": 56291,
                "MD5checksum": "5825f2e18e1695c2d030b9f6eexample"
            }]
        });

        let result: Manifest = serde_json::from_value(manifest).unwrap();
        assert_eq!(result, Manifest {
            destination_bucket: "arn:aws:s3:::example-destination-bucket".to_string(),
            file_format: InventoryFormat::Parquet,
            file_schema: "message s3.inventory { required binary bucket (UTF8); \
                required binary key (UTF8); optional binary version_id (UTF8); \
                optional boolean is_latest; optional boolean is_delete_marker; \
                optional int64 size; optional int64 last_modified_date (TIMESTAMP_MILLIS); \
                optional binary e_tag (UTF8); optional binary storage_class (UTF8); \
                optional boolean is_multipart_uploaded; optional binary replication_status (UTF8); \
                optional binary encryption_status (UTF8); \
                optional int64 object_lock_retain_until_date (TIMESTAMP_MILLIS); \
                optional binary object_lock_mode (UTF8); \
                optional binary object_lock_legal_hold_status (UTF8); \
                optional binary intelligent_tiering_access_tier (UTF8); \
                optional binary bucket_key_status (UTF8); optional binary checksum_algorithm (UTF8); \
                optional binary object_access_control_list (UTF8); \
                optional binary object_owner (UTF8);}".to_string(),
            files: vec![File {
                key: "inventory/example-source-bucket/data/d754c470-85bb-4255-9218-47023c8b4910.parquet".to_string(),
                md5_checksum: "5825f2e18e1695c2d030b9f6eexample".to_string(),
            }],
        });
    }

    fn expected_csv_manifest() -> Manifest {
        Manifest {
            destination_bucket: "arn:aws:s3:::example-inventory-destination-bucket".to_string(),
            file_format: InventoryFormat::Csv,
            file_schema: "Bucket, Key, VersionId, IsLatest, IsDeleteMarker, Size, \
                LastModifiedDate, ETag, StorageClass, IsMultipartUploaded, ReplicationStatus, \
                EncryptionStatus, ObjectLockRetainUntilDate, ObjectLockMode, \
                ObjectLockLegalHoldStatus, IntelligentTieringAccessTier, BucketKeyStatus, \
                ChecksumAlgorithm, ObjectAccessControlList, ObjectOwner".to_string(),
            files: vec![File {
                key: "Inventory/example-source-bucket/2016-11-06T21-32Z/files/939c6d46-85a9-4ba8-87bd-9db705a579ce.csv.gz".to_string(),
                md5_checksum: "f11166069f1990abeb9c97ace9cdfabc".to_string(), // pragma: allowlist secret
            }]
        }
    }
}
