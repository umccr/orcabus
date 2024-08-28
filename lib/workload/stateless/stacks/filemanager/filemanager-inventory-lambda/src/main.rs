use lambda_runtime::{run, service_fn, Error, LambdaEvent};
use serde::Deserialize;

use filemanager::clients::aws::s3::Client;
use filemanager::database::Client as DbClient;
use filemanager::env::Config;
use filemanager::events::aws::inventory::Manifest;
use filemanager::handlers::aws::{create_database_pool, ingest_s3_inventory, update_credentials};
use filemanager::handlers::init_tracing;

/// The Lambda request for the S3 inventory function.
#[derive(Debug, Deserialize, Eq, PartialEq)]
#[serde(untagged)]
pub enum Request {
    BucketKey(BucketKey),
    Manifest(Manifest),
}

/// The bucket and key which points to a manifest.json or manifest.checksum.
#[derive(Debug, Deserialize, Eq, PartialEq)]
pub struct BucketKey {
    bucket: String,
    key: String,
}

#[tokio::main]
async fn main() -> Result<(), Error> {
    init_tracing();

    let config = &Config::load()?;
    let options = &create_database_pool(config).await?;
    run(service_fn(|event: LambdaEvent<Request>| async move {
        update_credentials(options, config).await?;

        let client = Client::with_defaults().await;
        let database = DbClient::new(options.clone());

        match event.payload {
            Request::BucketKey(bucket_key) => {
                ingest_s3_inventory(
                    client,
                    database,
                    Some(bucket_key.bucket),
                    Some(bucket_key.key),
                    None,
                    config,
                )
                .await?
            }
            Request::Manifest(manifest) => {
                ingest_s3_inventory(client, database, None, None, Some(manifest), config).await?
            }
        };

        Ok::<_, Error>(())
    }))
    .await
}

#[cfg(test)]
mod tests {
    use aws_sdk_s3::types::InventoryFormat;
    use serde_json::{from_str, json};

    use filemanager::events::aws::inventory::File;

    use super::*;

    #[test]
    fn deserialize_bucket_key() {
        let bucket_key = json!({
            "bucket": "bucket",
            "key": "key"
        })
        .to_string();

        let result = from_str::<Request>(&bucket_key).unwrap();
        assert_eq!(
            result,
            Request::BucketKey(BucketKey {
                bucket: "bucket".to_string(),
                key: "key".to_string(),
            })
        );
    }

    #[test]
    fn deserialize_manifest() {
        let expected_checksum = "d41d8cd98f00b204e9800998ecf8427e"; // pragma: allowlist secret
        let expected_schema = "Bucket, Key, VersionId, IsLatest, IsDeleteMarker, Size, LastModifiedDate, ETag, StorageClass";
        let manifest = json!({
            "sourceBucket": "example-source-bucket",
            "destinationBucket": "arn:aws:s3:::example-inventory-destination-bucket",
            "version": "2016-11-30",
            "creationTimestamp" : "1514944800000",
            "fileFormat": "CSV",
            "fileSchema": expected_schema,
            "files": [
                {
                    "key": "key.csv.gz",
                    "size": 2147483647,
                    "MD5checksum": expected_checksum
                }
            ]
        })
        .to_string();

        assert_manifest(
            &manifest,
            Some(expected_schema.to_string()),
            Some(expected_checksum.to_string()),
            "arn:aws:s3:::example-inventory-destination-bucket",
        );
    }

    #[test]
    fn deserialize_manifest_minimal() {
        let manifest = json!({
            "destinationBucket": "example-inventory-destination-bucket",
            "fileFormat": "CSV",
            "files": [
                {
                    "key": "key.csv.gz"
                }
            ]
        })
        .to_string();

        assert_manifest(
            &manifest,
            None,
            None,
            "example-inventory-destination-bucket",
        );
    }

    fn assert_manifest(
        manifest: &str,
        file_schema: Option<String>,
        checksum: Option<String>,
        bucket: &str,
    ) {
        let result = from_str::<Request>(manifest).unwrap();
        let expected = Manifest::new(
            bucket.to_string(),
            InventoryFormat::Csv,
            file_schema,
            vec![File::new("key.csv.gz".to_string(), checksum)],
        );

        assert_eq!(result, Request::Manifest(expected));
    }
}
