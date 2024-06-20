//! Integration tests for S3 inventory.

use aws_sdk_s3::operation::get_object::GetObjectOutput;
use aws_sdk_s3::primitives::ByteStream;
use aws_smithy_mocks_experimental::{mock, mock_client, Rule, RuleMode};

use filemanager::clients::aws::s3::Client;
use filemanager::events::aws::inventory::{Inventory, Record};
use filemanager::events::aws::StorageClass;

/// Create mocks for the inventory manifest and inventory files.
macro_rules! base_mocks {
    ($bucket:expr, $inventory_file:expr, $manifest_file:expr) => {{
        const MANIFEST_JSON: &[u8] = include_bytes!(concat!("data/", $manifest_file));
        const INVENTORY: &[u8] = include_bytes!(concat!("data/", $inventory_file));

        let get_inventory_manifest = mock_get_object($bucket, $manifest_file, MANIFEST_JSON);
        let get_inventory = mock_get_object($bucket, $inventory_file, INVENTORY);

        (get_inventory_manifest, get_inventory)
    }};
}

/// Create a mock client. This is a macro so that file byte data can be included at compile time.
macro_rules! mock_client_for_inventory {
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
        let get_inventory_checksum = mock_get_object($bucket, $checksum_file, MANIFEST_CHECKSUM);

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

/// Mock a single GetObject request with the bucket, key and data.
fn mock_get_object(bucket: &'static str, key: &'static str, data: &'static [u8]) -> Rule {
    mock!(aws_sdk_s3::Client::get_object)
        .match_requests(|req| req.bucket() == Some(bucket) && req.key() == Some(key))
        .then_output(move || {
            GetObjectOutput::builder()
                .body(ByteStream::from_static(data))
                .build()
        })
}

/// Get records from an inventory.
async fn parse_records(client: aws_sdk_s3::Client, bucket: &str, file: &str) -> Vec<Record> {
    let inventory = Inventory::new(Client::new(client));

    inventory.parse_manifest_key(file, bucket).await.unwrap()
}

fn expected_records() -> Vec<Record> {
    let no_version_records = expected_records_no_version();
    vec![
        no_version_records[0].clone().set_is_delete_marker(false),
        Record::builder()
            .with_size(0)
            .with_last_modified_date("2024-05-06T22:38:00Z".parse().unwrap())
            .with_e_tag("d41d8cd98f00b204e9800998ecf8427e".to_string()) // pragma: allowlist secret
            .with_storage_class(StorageClass::Standard)
            .with_delete_marker(Some(false))
            .build(
                "filemanager-inventory-test".to_string(),
                "inventory-test/key1".to_string(),
            ),
        no_version_records[1]
            .clone()
            .set_version_id("tpinzcbxOfWpZsmjvVgdHEvSohsY4TA0".to_string())
            .set_is_delete_marker(false),
        Record::builder()
            .with_version_id("gdN1exfZmD7m713patv8dlQ7fTNwle3v".to_string())
            .with_last_modified_date("2024-05-06T22:46:14Z".parse().unwrap())
            .with_delete_marker(Some(true))
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
            .with_delete_marker(Some(false))
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
    let client = mock_client_for_inventory!(
        "filemanager-inventory-test",
        "csv_inventory.csv.gz",
        "csv_inventory_manifest.json",
        "csv_inventory_manifest.checksum"
    );
    let result = parse_records(
        client,
        "filemanager-inventory-test",
        "csv_inventory_manifest.checksum",
    )
    .await;
    assert_eq!(result, expected_records());
}

#[tokio::test]
async fn csv_with_manifest() {
    let client = mock_client_for_inventory!(
        "filemanager-inventory-test",
        "csv_inventory.csv.gz",
        "csv_inventory_manifest.json"
    );
    let result = parse_records(
        client,
        "filemanager-inventory-test",
        "csv_inventory_manifest.json",
    )
    .await;
    assert_eq!(result, expected_records());
}

#[tokio::test]
async fn csv_no_version_with_checksum() {
    let client = mock_client_for_inventory!(
        "filemanager-inventory-test",
        "csv_inventory_no_version.csv.gz",
        "csv_inventory_no_version_manifest.json",
        "csv_inventory_no_version_manifest.checksum"
    );
    let result = parse_records(
        client,
        "filemanager-inventory-test",
        "csv_inventory_no_version_manifest.checksum",
    )
    .await;
    assert_eq!(result, expected_records_no_version());
}

#[tokio::test]
async fn csv_no_version_with_manifest() {
    let client = mock_client_for_inventory!(
        "filemanager-inventory-test",
        "csv_inventory_no_version.csv.gz",
        "csv_inventory_no_version_manifest.json"
    );
    let result = parse_records(
        client,
        "filemanager-inventory-test",
        "csv_inventory_no_version_manifest.json",
    )
    .await;
    assert_eq!(result, expected_records_no_version());
}

#[tokio::test]
async fn orc_with_checksum() {
    let client = mock_client_for_inventory!(
        "filemanager-inventory-test",
        "orc_inventory.orc",
        "orc_inventory_manifest.json",
        "orc_inventory_manifest.checksum"
    );
    let result = parse_records(
        client,
        "filemanager-inventory-test",
        "orc_inventory_manifest.checksum",
    )
    .await;
    assert_eq!(result, expected_records());
}

#[tokio::test]
async fn orc_with_manifest() {
    let client = mock_client_for_inventory!(
        "filemanager-inventory-test",
        "orc_inventory.orc",
        "orc_inventory_manifest.json"
    );
    let result = parse_records(
        client,
        "filemanager-inventory-test",
        "orc_inventory_manifest.json",
    )
    .await;
    assert_eq!(result, expected_records());
}

#[tokio::test]
async fn parquet_with_checksum() {
    let client = mock_client_for_inventory!(
        "filemanager-inventory-test",
        "parquet_inventory.parquet",
        "parquet_inventory_manifest.json",
        "parquet_inventory_manifest.checksum"
    );
    let result = parse_records(
        client,
        "filemanager-inventory-test",
        "parquet_inventory_manifest.checksum",
    )
    .await;
    assert_eq!(result, expected_records());
}

#[tokio::test]
async fn parquet_with_manifest() {
    let client = mock_client_for_inventory!(
        "filemanager-inventory-test",
        "parquet_inventory.parquet",
        "parquet_inventory_manifest.json"
    );
    let result = parse_records(
        client,
        "filemanager-inventory-test",
        "parquet_inventory_manifest.json",
    )
    .await;
    assert_eq!(result, expected_records());
}
