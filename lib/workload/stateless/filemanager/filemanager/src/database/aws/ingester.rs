use aws_sdk_s3::operation::head_object::HeadObjectOutput;
use futures::future::join_all;
use futures::StreamExt;
use sqlx::{Executor, Postgres, QueryBuilder};
use uuid::Uuid;
use crate::database::DbClient;
use crate::events::aws::{EventType, FlatS3EventMessage, FlatS3EventMessages, TransposedS3EventMessages};
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
        let transposed_events = TransposedS3EventMessages::from(events);

        transposed_events.event_times.into_iter().group

        let mut events = join_all(events.into_inner().into_iter().map(|event| async move {
            let head = self.s3.head(&event.key, &event.bucket).await?;
            let uuid = Uuid::new_v4();

            Ok((event, head, uuid))
        })).await.into_iter().collect::<Result<Vec<_>>>()?.into_iter().peekable();

        while let Some(_) = events.peek() {
            events.take(BIND_LIMIT / 4).for_each(|(event, head, uuid)| {
                if let EventType::ObjectCreated = event.event_type {
                    let last_modified = head.map(|head| S3::convert_datetime(head.last_modified().cloned())).flatten().unwrap_or(event.event_time.clone());
                    let portal_run_id = event.event_time.format("%Y%m%d").to_string() + &uuid[..8];
                    query_builder_object.push_bind(uuid.to_string())
                        .push_bind(event.bucket)
                        .push_bind(event.key)
                        .push_bind(event.size)
                        .push_bind(event.e_tag)
                        .push_bind(event.event_time)
                        .push_bind(last_modified)
                        .push_bind(None)
                        .push_bind(portal_run_id);
                }

                if let EventType::ObjectRemoved = event.event_type {

                }
            });

            query_builder_object.push_values(events.take(BIND_LIMIT / 4), |mut b, (event, head, uuid)| {
                if let EventType::ObjectCreated = event.event_type {
                    let last_modified = head.map(|head| S3::convert_datetime(head.last_modified().cloned())).flatten().unwrap_or(event.event_time.clone());
                    let portal_run_id = event.event_time.format("%Y%m%d").to_string() + &uuid[..8];
                    b.push_bind(uuid.to_string())
                        .push_bind(event.bucket)
                        .push_bind(event.key)
                        .push_bind(event.size)
                        .push_bind(event.e_tag)
                        .push_bind(event.event_time)
                        .push_bind(last_modified)
                        .push_bind(None)
                        .push_bind(portal_run_id);
                }

                if let EventType::ObjectRemoved = event.event_type {

                }


                if let Some(head) = head {
                    b.push_bind(uuid.to_string())
                        .push_bind(event.bucket)
                        .push_bind(event.key)
                        .push_bind(event.size)
                        .push_bind(event.e_tag)
                        .push_bind(head.cr));
                }

                b.push_bind(uuid.to_string())
                    .push_bind(event.bucket)
                    .push_bind(event.key)
                    .push_bind(event.size)
                    .push_bind(event.e_tag)
                    .push_bind());
            });
        }

        events.take(BIND_LIMIT / 4)

        query_builder_object.ta

        for event in events.into_inner() {
            let head = self.s3.head(&event.key, &event.bucket).await?;
            let uuid = Uuid::new_v4();

            query_builder_object.push()
            todo!();


        }

        Ok(())
    }
}