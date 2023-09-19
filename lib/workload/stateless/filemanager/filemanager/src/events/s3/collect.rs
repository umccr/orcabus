use crate::error::Result;
use crate::events::s3::s3::S3;
use crate::events::s3::{Events, FlatS3EventMessages};
use crate::events::{Collect, EventType};
use async_trait::async_trait;

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
            raw_events,
        })
    }
}

#[async_trait]
impl Collect for Collecter {
    async fn collect(self) -> Result<EventType> {
        let events = self.s3.update_events(self.raw_events).await?;

        Ok(EventType::S3(Events::from(events)))
    }
}
