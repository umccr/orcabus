// use aws_config::meta::region::RegionProviderChain;
use crate::db::DbClient;
use crate::error::Error::{SQSClientError, SQSDeserializeError, SQSReceiveError, S3Error, DbClientError};
use crate::error::Result;
use aws_sdk_s3::operation::head_object::{HeadObjectOutput, HeadObjectError};
use aws_sdk_sqs::Client;
use aws_sdk_s3::Client as S3Client;
use serde::{Deserialize, Serialize};

#[derive(Debug)]
pub struct SQSClient {
    client: Client,
    url: String,
    db: DbClient,
    s3_client: S3Client,
}

impl SQSClient {
    pub fn new(client: Client, url: String, db: DbClient, s3_client: S3Client) -> Self {
        Self { client, url, db, s3_client }
    }

    pub async fn with_default_client() -> Result<Self> {
        let config = aws_config::from_env()
        .endpoint_url(
            std::env::var("ENDPOINT_URL")
                .map_err(|err| SQSClientError(err.to_string()))?,
        )
        .load()
        .await;

        Ok(Self {
            client: Client::new(&config),
            url: std::env::var("SQS_QUEUE_URL").map_err(|err| DbClientError(err.to_string()))?,
            db: DbClient::with_default_client().await?,
            s3_client: S3Client::new(&config),
        })
    }

    /// Gets some S3 metadata from HEAD such as (creation/archival) timestamps and statuses
    pub async fn s3_head(&self, key: &str, bucket: &str) -> Result<Option<HeadObjectOutput>> {
        let head = self
            .s3_client
            .head_object()
            .bucket(bucket)
            .key(key)
            .send()
            .await;

        match head {
            Ok(head) => Ok(Some(head)),
            Err(err) => {
                let err = err.into_service_error();
                if let HeadObjectError::NotFound(_) = err {
                    // Object not found, could be deleted.
                    Ok(None)
                } else {
                    // I.e: Cannot connect to server
                    Err(S3Error(err.to_string()))
                }
            }
        }
    }

    // TODO: Two possible event types, should be handled differently: PUT and DELETE
    pub async fn receive(&self) -> Result<()> {
        let rcv_message_output = self
            .client
            .receive_message()
            .queue_url(&self.url)
            .send()
            .await
            .map_err(|err| SQSReceiveError(err.into_service_error().to_string()))?;

        for message in rcv_message_output.messages.unwrap_or_default() {
            println!("Got the message: {:#?}", message);

            if let Some(body) = message.body() {
                let mut message: EventMessage = serde_json::from_str(body)
                    .map_err(|err| SQSDeserializeError(err.to_string()))?;
                

                for record in message.records.iter_mut() {
                    let head = self.s3_head(&record.s3.object.key, &record.s3.bucket.name).await?;
                    record.head = head;
                }

                self.db.ingest_s3_event(message).await?;
            }
        }

        Ok(())
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct EventMessage {
    #[serde(rename = "Records")]
    pub records: Vec<Record>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Record {
    pub s3: S3Record,
    #[serde(skip)]
    pub head: Option<HeadObjectOutput>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct S3Record {
    pub bucket: BucketRecord,
    pub object: ObjectRecord,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct BucketRecord {
    pub name: String,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ObjectRecord {
    pub key: String,
    pub size: i32,
    pub e_tag: String,
}
