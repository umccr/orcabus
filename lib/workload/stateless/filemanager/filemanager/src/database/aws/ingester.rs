use sqlx::{Executor, Postgres, QueryBuilder};
use uuid::Uuid;
use crate::database::DbClient;
use crate::events::aws::FlatS3EventMessages;
use crate::events::aws::s3::S3;
use crate::error::Result;

/// Postgres prepared statement bind limit.
const BIND_LIMIT: usize = 65535;

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
            s3: S3::with_default_client().await?
        })
    }

    pub async fn ingest_events(&self, events: FlatS3EventMessages) -> Result<()> {
        let mut query_builder_object: QueryBuilder<Postgres> = QueryBuilder::new(
            "INSERT INTO object (object_id, bucket, key, size, hash, created_date, last_modified_date, deleted_date, portal_run_id) ",
        );
        let mut query_builder_s3_object: QueryBuilder<Postgres> = QueryBuilder::new(
            "INSERT INTO s3_object (object_id, storage_class) ",
        );

        for event in events.into_inner() {
            let head = self.s3.head(&event.key, &event.bucket).await?;
            let uuid = Uuid::new_v4();

            todo!();


        }

        Ok(())
    }
}