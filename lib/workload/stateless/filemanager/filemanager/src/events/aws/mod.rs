use serde::{Deserialize, Serialize};

pub mod sqs;
pub mod s3;
pub mod ingester;

/// The basic AWS S3 Event.
#[derive(Debug, Serialize, Deserialize)]
pub struct S3EventMessage {
    #[serde(rename = "Records")]
    pub records: Vec<Record>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Record {
    pub s3: S3Record,
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