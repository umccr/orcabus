use filemanager::clients::aws::s3::Client;
use lambda_runtime::{run, service_fn, Error, LambdaEvent};
use serde::Deserialize;

use filemanager::database::Client as DbClient;
use filemanager::events::aws::inventory::Manifest;
use filemanager::handlers::aws::{create_database_pool, ingest_s3_inventory, update_credentials};
use filemanager::handlers::init_tracing;

/// The Lambda request for the S3 inventory function.
#[derive(Debug, Deserialize)]
pub enum Request {
    BucketKey(BucketKey),
    Manifest(Manifest),
}

/// The bucket and key which points to a manifest.json or manifest.checksum.
#[derive(Debug, Deserialize)]
pub struct BucketKey {
    bucket: String,
    key: String,
}

#[tokio::main]
async fn main() -> Result<(), Error> {
    init_tracing();

    let options = &create_database_pool().await?;
    run(service_fn(|event: LambdaEvent<Request>| async move {
        update_credentials(options).await?;

        let client = Client::with_defaults().await;
        let database = DbClient::from_ref(options);

        match event.payload {
            Request::BucketKey(bucket_key) => {
                ingest_s3_inventory(
                    client,
                    database,
                    Some(bucket_key.bucket),
                    Some(bucket_key.key),
                    None,
                )
                .await?
            }
            Request::Manifest(manifest) => {
                ingest_s3_inventory(client, database, None, None, Some(manifest)).await?
            }
        };

        Ok::<_, Error>(())
    }))
    .await
}
