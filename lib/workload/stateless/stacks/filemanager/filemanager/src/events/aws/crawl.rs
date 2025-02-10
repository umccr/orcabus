//! Crawl S3 using list operations and ingest into the database.
//!

#[double]
use crate::clients::aws::s3::Client;
use crate::database::entities::sea_orm_active_enums::Reason;
use crate::error::Result;
use crate::events::aws::message::{
    default_version_id, quote_e_tag, Bucket, EventType, EventTypeData, EventTypeParsed, Record,
    S3Record,
};
use crate::events::aws::{empty_sequencer, FlatS3EventMessage, FlatS3EventMessages};
use crate::uuid::UuidGenerator;
use aws_sdk_s3::types::Object;
use chrono::Utc;
use mockall_double::double;

/// Represents crawl operations.
#[derive(Debug)]
pub struct Crawl {
    client: Client,
}

impl Crawl {
    /// Create a new crawl.
    pub fn new(client: Client) -> Self {
        Self { client }
    }

    /// Create a new crawl with a default s3 client.
    pub async fn with_defaults() -> Self {
        Self::new(Client::with_defaults().await)
    }

    /// Crawl S3 and produce the event messages that should be ingested.
    pub async fn crawl_s3(
        &self,
        bucket: &str,
        prefix: Option<String>,
    ) -> Result<FlatS3EventMessages> {
        let list = self.client.list_objects(bucket, prefix).await?;

        let Some(contents) = list.contents else {
            return Ok(FlatS3EventMessages::default());
        };

        Ok(FlatS3EventMessages(
            contents
                .into_iter()
                .map(|object| FlatS3EventMessage::from(object).with_bucket(bucket.to_string()))
                .collect(),
        ))
    }
}

impl From<Object> for FlatS3EventMessage {
    fn from(object: Object) -> Self {
        let Object {
            key,
            e_tag,
            size,
            restore_status,
            ..
        } = object;

        let reason = match restore_status.and_then(|status| status.restore_expiry_date) {
            Some(_) => Reason::CrawlRestored,
            _ => Reason::Crawl,
        };

        Self {
            s3_object_id: UuidGenerator::generate(),
            event_time: Some(Utc::now()),
            // This is set later.
            bucket: "".to_string(),
            key: key.unwrap_or_default(),
            size,
            e_tag: e_tag.map(quote_e_tag),
            // Set this to the empty string so that any deleted events after this can bind to this
            // created event, as they are always greater than this event.
            sequencer: Some(empty_sequencer()),
            version_id: default_version_id(),
            // Head fields are fetched later.
            storage_class: None,
            last_modified_date: None,
            sha256: None,
            // A crawl record is a created event
            event_type: EventType::Created,
            is_current_state: true,
            is_delete_marker: false,
            reason,
            archive_status: None,
            ingest_id: None,
            attributes: None,
            number_duplicate_events: 0,
            number_reordered: 0,
        }
    }
}

#[cfg(test)]
pub(crate) mod tests {
    use super::*;
    use crate::events::aws::message::EventType::Created;
    use crate::events::aws::tests::assert_flat_without_time;
    use crate::events::aws::tests::EXPECTED_QUOTED_E_TAG;
    use aws_sdk_s3::operation::list_objects_v2::ListObjectsV2Output;
    use chrono::DateTime;
    use mockall::predicate::eq;
    use uuid::Uuid;

    #[tokio::test]
    async fn crawl_messages() {
        let mut client = Client::default();
        client
            .expect_list_objects()
            .with(eq("bucket"), eq(Some("prefix".to_string())))
            .once()
            .returning(move |_, _| {
                Ok(ListObjectsV2Output::builder()
                    .contents(
                        Object::builder()
                            .key("key")
                            .size(1)
                            .e_tag(EXPECTED_QUOTED_E_TAG)
                            .build(),
                    )
                    .contents(
                        Object::builder()
                            .key("key")
                            .size(2)
                            .e_tag(EXPECTED_QUOTED_E_TAG)
                            .build(),
                    )
                    .build())
            });

        let result = Crawl::new(client)
            .crawl_s3("bucket", Some("prefix".to_string()))
            .await
            .unwrap()
            .into_inner();

        assert_flat_without_time(
            result[0].clone(),
            &Created,
            Some(empty_sequencer()),
            Some(1),
            default_version_id(),
            false,
            true,
        );
        assert_flat_without_time(
            result[1].clone(),
            &Created,
            Some(empty_sequencer()),
            Some(2),
            default_version_id(),
            false,
            true,
        );
    }
}
