use async_trait::async_trait;
use chrono::{DateTime, Utc};
use sqlx::query_file;
use tracing::trace;

use crate::database::{DbClient, Ingest};
use crate::error::Result;
use crate::events::s3::StorageClass;
use crate::events::s3::{Events, TransposedS3EventMessages};
use crate::events::EventType;

/// An ingester for S3 events.
#[derive(Debug)]
pub struct Ingester {
    db: DbClient,
}

impl Ingester {
    pub fn new(db: DbClient) -> Self {
        Self { db }
    }

    pub async fn new_with_defaults() -> Result<Self> {
        Ok(Self {
            db: DbClient::new_with_defaults().await?,
        })
    }

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
        .execute(&self.db.pool)
        .await?;

        query_file!(
            "../database/queries/ingester/aws/insert_s3_objects.sql",
            &object_ids,
            &storage_classes as &[Option<StorageClass>]
        )
        .execute(&self.db.pool)
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
        .execute(&self.db.pool)
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
