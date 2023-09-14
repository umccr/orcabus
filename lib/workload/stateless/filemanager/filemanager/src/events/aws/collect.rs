use crate::events::aws::s3::S3;
use crate::error::Result;
use crate::events::aws::sqs::SQS;
use crate::events::{Collect, EventType};
use crate::events::aws::{Events, FlatS3EventMessages};

#[derive(Debug)]
pub struct Collecter {
    s3: S3,
    raw_events: FlatS3EventMessages,
}

impl Collecter {
    pub fn new(s3: S3, raw_events: FlatS3EventMessages) -> Self {
        Self { s3, raw_events }
    }

    pub async fn with_defaults(raw_events: FlatS3EventMessages) -> Result<Self> {
        Ok(Self {
            s3: S3::with_defaults().await?,
            raw_events
        })
    }
}

impl Collect for Collecter {
    fn collect(self) -> Result<EventType> {
        Ok(EventType::S3(Events::from(self.raw_events)))
    }
}