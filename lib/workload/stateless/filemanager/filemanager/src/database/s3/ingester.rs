use sqlx::query_file;

use crate::database::DbClient;
use crate::error::Result;
use crate::events::s3::s3::S3;
use crate::events::s3::{Events, TransposedS3EventMessages};

/// An ingester for S3 events.
#[derive(Debug)]
pub struct Ingester {
    db: DbClient,
    s3: S3,
}

impl Ingester {
    pub fn new(db: DbClient, s3: S3) -> Self {
        Self { db, s3 }
    }

    pub async fn new_with_defaults() -> Result<Self> {
        Ok(Self {
            db: DbClient::new_with_defaults().await?,
            s3: S3::with_defaults().await?,
        })
    }

    pub async fn ingest_events(&mut self, events: Events) -> Result<()> {
        let Events {
            object_created,
            object_removed,
            ..
        } = events;

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
