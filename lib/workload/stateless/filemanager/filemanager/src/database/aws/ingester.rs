use aws_sdk_s3::operation::head_object::HeadObjectOutput;
use futures::future::join_all;
use futures::StreamExt;
use sqlx::{Executor, Postgres, query_file, QueryBuilder};
use uuid::Uuid;
use crate::database::DbClient;
use crate::events::aws::{Events, FlatS3EventMessage, FlatS3EventMessages, TransposedS3EventMessages};
use crate::events::aws::s3::S3;
use crate::error::Result;

/// An ingester for S3 events.
#[derive(Debug)]
pub struct Ingester {
    db: DbClient,
    s3: S3
}

impl Ingester {
    pub fn new(db: DbClient, s3: S3) -> Self {
        Self { db, s3 }
    }

    pub async fn new_with_defaults() -> Result<Self> {
        Ok(Self {
            db: DbClient::new_with_defaults().await?,
            s3: S3::with_defaults().await?
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
            event_names,
            buckets,
            keys,
            sizes,
            e_tags,
            sequencers,
            portal_run_ids,
            storage_classes,
            last_modified_dates
        } = object_created;

        query_file!("queries/ingester/insert_objects.sql", object_ids, buckets, keys, sizes, e_tags, event_times, last_modified_dates, vec![None; object_ids.len()], portal_run_ids)
            .execute(&mut self.db.pool)
            .await?;

        query_file!("queries/ingester/aws/insert_s3_objects.sql", object_ids, storage_classes)
            .execute(&mut self.db.pool)
            .await?;

        let TransposedS3EventMessages {
            object_ids,
            event_times,
            event_names,
            buckets,
            keys,
            sizes,
            e_tags,
            sequencers,
            portal_run_ids,
            storage_classes,
            last_modified_dates
        } = object_removed;

        query_file!("queries/update_deleted.sql", keys, buckets, event_times)
            .execute(&mut self.db.pool)
            .await?;

        Ok(())
    }
}