use chrono::{DateTime, NaiveDateTime, Utc};
use futures::future::join_all;
use futures::{FutureExt, StreamExt};
use crate::database::aws::CloudObject;
use crate::database::CloudObject::S3 as S3CloudObject;
use crate::database::Object;
use crate::error::Error::S3Error;
use crate::events::aws::s3::S3;
use crate::events::aws::sqs::SQS;
use crate::error::Result;
use crate::events::aws::{BucketRecord, ObjectRecord, S3Record};

#[derive(Debug)]
pub struct Ingester {
    sqs: SQS,
    s3: S3,
}

impl Ingester {
    pub fn new(sqs: SQS, s3: S3) -> Self {
        Self {
            sqs,
            s3
        }
    }

    pub async fn with_default_client() -> Result<Self> {
        Ok(Self {
            sqs: SQS::with_default_client().await?,
            s3: S3::with_default_client().await?
        })
    }

    pub async fn ingest_s3_events(&self) -> Result<Vec<Object>> {
        let events = self.sqs.receive().await?;

        self.s3.ingest_s3_events(events).await
    }
}