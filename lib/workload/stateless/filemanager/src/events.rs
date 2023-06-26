// use aws_config::meta::region::RegionProviderChain;
use aws_sdk_sqs::Client;
use crate::error::Result;
use crate::error::Error::{SQSClientError, SQSReceiveError, SQSDeserializeError};
use serde::{Serialize, Deserialize};
use crate::db::DbClient;

#[derive(Debug)]
pub struct SQSClient {
    client: Client,
    url: String,
    db: DbClient, 
}

impl SQSClient {
    pub fn new(client: Client, url: String, db: DbClient) -> Self {
        Self {
            client,
            url,
            db
        }
    }

    pub async fn with_default_client() -> Result<Self> {
        Ok(Self {
            client: Client::new(&aws_config::from_env()
                .endpoint_url(std::env::var("ENDPOINT_URL").map_err(|err| SQSClientError(err.to_string()))?)
                .load().await),
            url: std::env!("SQS_QUEUE_URL").to_string(),
            db: DbClient::with_default_client().await?
        })
    }

    pub async fn receive(&self) -> Result<()> {
        let rcv_message_output = self.client.receive_message().queue_url(&self.url).send().await.map_err(|err| SQSReceiveError(err.into_service_error().to_string()))?;
    
        println!("Messages from queue with url: {}", &self.url);
    
        for message in rcv_message_output.messages.unwrap_or_default() {
            println!("Got the message: {:#?}", message);

            if let Some(body) = message.body() {
                let message: EventMessage = serde_json::from_str(body).map_err(|err| SQSDeserializeError(err.to_string()))?;
                self.db.ingest_s3_event(message).await?;
            }
        }
    
        Ok(())
    }    
}

#[derive(Debug, Serialize, Deserialize)]
pub struct EventMessage {
    #[serde(rename = "Records")]
    pub records: Vec<Record>
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Record {
    pub s3: S3Record
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