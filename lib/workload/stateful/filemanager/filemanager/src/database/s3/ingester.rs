use async_trait::async_trait;
use chrono::{DateTime, Utc};
use sqlx::query_file;
use tracing::trace;

use crate::database::{Client, Ingest};
use crate::error::Result;
use crate::events::s3::StorageClass;
use crate::events::s3::{Events, TransposedS3EventMessages};
use crate::events::EventType;

/// An ingester for S3 events.
#[derive(Debug)]
pub struct Ingester {
    client: Client,
}

impl Ingester {
    /// Create a new ingester.
    pub fn new(db: Client) -> Self {
        Self { client: db }
    }

    /// Create a new ingester with a default database client.
    pub async fn default() -> Result<Self> {
        Ok(Self {
            client: Client::default().await?,
        })
    }

    /// Ingest the events into the database by calling the insert and update queries.
    pub async fn ingest_s3_events(&mut self, events: Events) -> Result<()> {
        let Events {
            object_created,
            object_removed,
            ..
        } = events;

        trace!(object_created = ?object_created, "ingesting object created events");
        let TransposedS3EventMessages {
            object_ids,
            event_times,
            buckets,
            keys,
            sizes,
            e_tags,
            portal_run_ids,
            storage_classes,
            last_modified_dates,
            ..
        } = object_created;

        query_file!(
            "../database/queries/ingester/insert_objects.sql",
            &object_ids,
            &buckets,
            &keys,
            &sizes,
            &e_tags,
            &event_times,
            &last_modified_dates as &[Option<DateTime<Utc>>],
            &portal_run_ids
        )
        .execute(&self.client.pool)
        .await?;

        query_file!(
            "../database/queries/ingester/aws/insert_s3_objects.sql",
            &object_ids,
            &storage_classes as &[Option<StorageClass>]
        )
        .execute(&self.client.pool)
        .await?;

        trace!(object_removed = ?object_removed, "ingesting object removed events");
        let TransposedS3EventMessages {
            event_times,
            buckets,
            keys,
            ..
        } = object_removed;

        query_file!(
            "../database/queries/ingester/update_deleted.sql",
            &keys,
            &buckets,
            &event_times
        )
        .execute(&self.client.pool)
        .await?;

        Ok(())
    }
}

#[async_trait]
impl Ingest for Ingester {
    async fn ingest(&mut self, events: EventType) -> Result<()> {
        match events {
            EventType::S3(events) => self.ingest_s3_events(events).await,
        }
    }
}
