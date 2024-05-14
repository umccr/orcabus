//! Integration tests for S3 inventory.

use aws_sdk_s3::operation::get_object::GetObjectOutput;
use aws_sdk_s3::primitives::ByteStream;
use aws_smithy_mocks_experimental::{mock, mock_client, RuleMode};
use filemanager::clients::aws::s3::Client;
use filemanager::events::aws::inventory::{Inventory, Record};
use filemanager::events::aws::StorageClass;

/// Create mocks for the inventory manifest and inventory files.
macro_rules! base_mocks {
    ($bucket:expr, $inventory_file:expr, $manifest_file:expr) => {{
        const MANIFEST_JSON: &[u8] = include_bytes!(concat!("data/", $manifest_file));
        const INVENTORY: &[u8] = include_bytes!(concat!("data/", $inventory_file));

        let get_inventory_manifest = mock!(aws_sdk_s3::Client::get_object)
            .match_requests(|req| {
                req.bucket() == Some($bucket) && req.key() == Some($manifest_file)
            })
            .then_output(|| {
                GetObjectOutput::builder()
                    .body(ByteStream::from_static(MANIFEST_JSON))
                    .build()
            });

        let get_inventory = mock!(aws_sdk_s3::Client::get_object)
            .match_requests(|req| {
                req.bucket() == Some($bucket) && req.key() == Some($inventory_file)
            })
            .then_output(|| {
                GetObjectOutput::builder()
                    .body(ByteStream::from_static(INVENTORY))
                    .build()
            });

        (get_inventory_manifest, get_inventory)
    }};
}

/// Create a mock client. This is a macro so that file byte data can be included at compile time.
macro_rules! mock_client_for_inventory {
    (impl $bucket:expr, $inventory_file:expr, $manifest_file:expr) => {{
        const MANIFEST_JSON: &[u8] = include_bytes!(concat!("data/", $manifest_file));
        const INVENTORY: &[u8] = include_bytes!(concat!("data/", $inventory_file));

        let get_inventory_manifest = mock!(aws_sdk_s3::Client::get_object)
            .match_requests(|req| {
                req.bucket() == Some($bucket) && req.key() == Some($manifest_file)
            })
            .then_output(|| {
                GetObjectOutput::builder()
                    .body(ByteStream::from_static(MANIFEST_JSON))
                    .build()
            });

        let get_inventory = mock!(aws_sdk_s3::Client::get_object)
            .match_requests(|req| {
                req.bucket() == Some($bucket) && req.key() == Some($inventory_file)
            })
            .then_output(|| {
                GetObjectOutput::builder()
                    .body(ByteStream::from_static(INVENTORY))
                    .build()
            });

        (get_inventory_manifest, get_inventory)
    }};
    ($bucket:expr, $inventory_file:expr, $manifest_file:expr) => {{
        let (get_inventory_manifest, get_inventory) =
            base_mocks!($bucket, $inventory_file, $manifest_file);

        mock_client!(
            aws_sdk_s3,
            RuleMode::MatchAny,
            &[&get_inventory_manifest, &get_inventory]
        )
    }};
    ($bucket:expr, $inventory_file:expr, $manifest_file:expr, $checksum_file:expr) => {{
        let (get_inventory_manifest, get_inventory) =
            base_mocks!($bucket, $inventory_file, $manifest_file);

        const MANIFEST_CHECKSUM: &[u8] = include_bytes!(concat!("data/", $checksum_file));
        let get_inventory_checksum = mock!(aws_sdk_s3::Client::get_object)
            .match_requests(|req| {
                req.bucket() == Some($bucket) && req.key() == Some($checksum_file)
            })
            .then_output(|| {
                GetObjectOutput::builder()
                    .body(ByteStream::from_static(MANIFEST_CHECKSUM))
                    .build()
            });

        mock_client!(
            aws_sdk_s3,
            RuleMode::MatchAny,
            &[
                &get_inventory_checksum,
                &get_inventory_manifest,
                &get_inventory
            ]
        )
    }};
}

/// Get records from an inventory.
macro_rules! parse_records {
    ($bucket:expr, $inventory_file:expr, $manifest_file:expr) => {{
        let client = mock_client_for_inventory!($bucket, $inventory_file, $manifest_file);
        let inventory = Inventory::new(Client::new(client));

        inventory.parse_manifest_key($manifest_file, $bucket).await
    }};
    ($bucket:expr, $inventory_file:expr, $manifest_file:expr, $checksum_file:expr) => {{
        let client =
            mock_client_for_inventory!($bucket, $inventory_file, $manifest_file, $checksum_file);
        let inventory = Inventory::new(Client::new(client));

        inventory.parse_manifest_key($checksum_file, $bucket).await
    }};
}

fn expected_records() -> Vec<Record> {
    let no_version_records = expected_records_no_version();
    vec![
        no_version_records[0].clone(),
        Record::builder()
            .with_size(0)
            .with_last_modified_date("2024-05-06T22:38:00Z".parse().unwrap())
            .with_e_tag("d41d8cd98f00b204e9800998ecf8427e".to_string()) // pragma: allowlist secret
            .with_storage_class(StorageClass::Standard)
            .build(
                "filemanager-inventory-test".to_string(),
                "inventory-test/key1".to_string(),
            ),
        no_version_records[1]
            .clone()
            .set_version_id("tpinzcbxOfWpZsmjvVgdHEvSohsY4TA0".to_string()),
        Record::builder()
            .with_version_id("gdN1exfZmD7m713patv8dlQ7fTNwle3v".to_string())
            .with_last_modified_date("2024-05-06T22:46:14Z".parse().unwrap())
            .build(
                "filemanager-inventory-test".to_string(),
                "inventory-test/key2".to_string(),
            ),
        Record::builder()
            .with_version_id("zl_C7NLxrkBsMFD5HQUdybrmuV9VpvkN".to_string())
            .with_size(5)
            .with_last_modified_date("2024-05-06T22:45:34Z".parse().unwrap())
            .with_e_tag("d8e8fca2dc0f896fd7cb4cb0031ba249".to_string()) // pragma: allowlist secret
            .with_storage_class(StorageClass::Standard)
            .build(
                "filemanager-inventory-test".to_string(),
                "inventory-test/key2".to_string(),
            ),
    ]
}

fn expected_records_no_version() -> Vec<Record> {
    vec![
        Record::builder()
            .with_size(0)
            .with_last_modified_date("2024-05-06T22:37:48Z".parse().unwrap())
            .with_e_tag("d41d8cd98f00b204e9800998ecf8427e".to_string()) // pragma: allowlist secret
            .with_storage_class(StorageClass::Standard)
            .build(
                "filemanager-inventory-test".to_string(),
                "inventory-test/".to_string(),
            ),
        Record::builder()
            .with_size(5)
            .with_last_modified_date("2024-05-06T22:44:22Z".parse().unwrap())
            .with_e_tag("d8e8fca2dc0f896fd7cb4cb0031ba249".to_string()) // pragma: allowlist secret
            .with_storage_class(StorageClass::Standard)
            .build(
                "filemanager-inventory-test".to_string(),
                "inventory-test/key1".to_string(),
            ),
    ]
}

#[tokio::test]
async fn csv_with_checksum() {
    let result = parse_records!(
        "filemanager-inventory-test",
        "csv_inventory.csv.gz",
        "csv_inventory_manifest.json",
        "csv_inventory_manifest.checksum"
    );
    assert_eq!(result.unwrap(), expected_records());
}

#[tokio::test]
async fn csv_with_manifest() {
    let result = parse_records!(
        "filemanager-inventory-test",
        "csv_inventory.csv.gz",
        "csv_inventory_manifest.json"
    );
    assert_eq!(result.unwrap(), expected_records());
}

#[tokio::test]
async fn csv_no_version_with_checksum() {
    let result = parse_records!(
        "filemanager-inventory-test",
        "csv_inventory_no_version.csv.gz",
        "csv_inventory_no_version_manifest.json",
        "csv_inventory_no_version_manifest.checksum"
    );
    assert_eq!(result.unwrap(), expected_records_no_version());
}

#[tokio::test]
async fn csv_no_version_with_manifest() {
    let result = parse_records!(
        "filemanager-inventory-test",
        "csv_inventory_no_version.csv.gz",
        "csv_inventory_no_version_manifest.json"
    );
    assert_eq!(result.unwrap(), expected_records_no_version());
}

#[tokio::test]
async fn orc_with_checksum() {
    let result = parse_records!(
        "filemanager-inventory-test",
        "orc_inventory.orc",
        "orc_inventory_manifest.json",
        "orc_inventory_manifest.checksum"
    );
    assert_eq!(result.unwrap(), expected_records());
}

#[tokio::test]
async fn orc_with_manifest() {
    let result = parse_records!(
        "filemanager-inventory-test",
        "orc_inventory.orc",
        "orc_inventory_manifest.json"
    );
    assert_eq!(result.unwrap(), expected_records());
}

#[tokio::test]
async fn parquet_with_checksum() {
    let result = parse_records!(
        "filemanager-inventory-test",
        "parquet_inventory.parquet",
        "parquet_inventory_manifest.json",
        "parquet_inventory_manifest.checksum"
    );
    assert_eq!(result.unwrap(), expected_records());
}

#[tokio::test]
async fn parquet_with_manifest() {
    let result = parse_records!(
        "filemanager-inventory-test",
        "parquet_inventory.parquet",
        "parquet_inventory_manifest.json"
    );
    assert_eq!(result.unwrap(), expected_records());
}
