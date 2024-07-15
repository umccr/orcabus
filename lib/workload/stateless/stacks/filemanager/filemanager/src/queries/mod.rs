//! This module handles all logic related to querying the file manager through APIs/events.
//!

pub mod get;
pub mod list;

#[cfg(test)]
pub(crate) mod tests {
    use std::ops::Add;

    use chrono::{DateTime, Days};
    use rand::seq::SliceRandom;
    use rand::thread_rng;
    use sea_orm::Set;
    use sea_orm::{ActiveModelTrait, TryIntoModel};
    use serde_json::json;
    use strum::EnumCount;

    use crate::database::entities::object::ActiveModel as ActiveObject;
    use crate::database::entities::object::Model as Object;
    use crate::database::entities::s3_object::ActiveModel as ActiveS3Object;
    use crate::database::entities::s3_object::Model as S3Object;
    use crate::database::entities::sea_orm_active_enums::{EventType, StorageClass};
    use crate::database::Client;
    use crate::uuid::UuidGenerator;

    /// Container for generated database entries
    pub(crate) struct Entries {
        pub(crate) objects: Vec<Object>,
        pub(crate) s3_objects: Vec<S3Object>,
    }

    impl From<Vec<(Object, S3Object)>> for Entries {
        fn from(objects: Vec<(Object, S3Object)>) -> Self {
            let (objects, s3_objects) = objects.into_iter().unzip();
            Self {
                objects,
                s3_objects,
            }
        }
    }

    /// Initialize the database state for testing and shuffle entries to simulate
    /// out of order events.
    pub(crate) async fn initialize_database_reorder(client: &Client, n: usize) -> Entries {
        initialize_database_ratios_reorder(client, n, 2, 1).await
    }

    /// Initialize database state for testing.
    pub(crate) async fn initialize_database(client: &Client, n: usize) -> Entries {
        initialize_database_with_shuffle(client, n, false, 2, 1)
            .await
            .into()
    }

    /// Initialize database state for testing with custom bucket and key ratios of Created/Deleted
    /// events and out of order events.
    pub(crate) async fn initialize_database_ratios_reorder(
        client: &Client,
        n: usize,
        bucket_ratio: usize,
        key_ratio: usize,
    ) -> Entries {
        let mut data =
            initialize_database_with_shuffle(client, n, true, bucket_ratio, key_ratio).await;

        // Return the correct ordering for test purposes
        data.sort_by(|(_, a), (_, b)| a.sequencer.cmp(&b.sequencer));

        data.into()
    }

    async fn initialize_database_with_shuffle(
        client: &Client,
        n: usize,
        shuffle: bool,
        bucket_ratio: usize,
        key_ratio: usize,
    ) -> Vec<(Object, S3Object)> {
        let mut output = vec![];

        let mut entries: Vec<_> = (0..n)
            .map(|index| generate_entry(index, bucket_ratio, key_ratio))
            .collect();

        if shuffle {
            entries.shuffle(&mut thread_rng());
        }

        for (object, s3_object) in entries {
            object
                .clone()
                .insert(client.connection_ref())
                .await
                .unwrap();
            s3_object
                .clone()
                .insert(client.connection_ref())
                .await
                .unwrap();

            output.push((
                object.try_into_model().unwrap(),
                s3_object.try_into_model().unwrap(),
            ));
        }

        output
    }

    pub(crate) fn generate_entry(
        index: usize,
        bucket_ratio: usize,
        key_ratio: usize,
    ) -> (ActiveObject, ActiveS3Object) {
        let object_id = UuidGenerator::generate();
        let event = event_type(index);
        let date = || Set(Some(DateTime::default().add(Days::new(index as u64))));
        let attributes = Some(json!({
            "attribute_id": format!("{}", index),
            "nested_id": {
                "attribute_id": format!("{}", index)
            }
        }));

        (
            ActiveObject {
                object_id: Set(object_id),
                attributes: Set(attributes.clone()),
            },
            ActiveS3Object {
                s3_object_id: Set(UuidGenerator::generate()),
                object_id: Set(object_id),
                public_id: Set(UuidGenerator::generate()),
                event_type: Set(event.clone()),
                bucket: Set((index / bucket_ratio).to_string()),
                key: Set((index / key_ratio).to_string()),
                version_id: Set((index / key_ratio).to_string()),
                date: date(),
                size: Set(Some(index as i64)),
                sha256: Set(Some(index.to_string())),
                last_modified_date: date(),
                e_tag: Set(Some(index.to_string())),
                storage_class: Set(Some(storage_class(index))),
                sequencer: Set(Some(index.to_string())),
                is_delete_marker: Set(false),
                number_duplicate_events: Set(0),
                attributes: Set(attributes),
                deleted_date: if event == EventType::Deleted {
                    date()
                } else {
                    Set(None)
                },
                deleted_sequencer: if event == EventType::Deleted {
                    Set(Some(index.to_string()))
                } else {
                    Set(None)
                },
                number_reordered: Set(0),
            },
        )
    }

    pub(crate) fn event_type(index: usize) -> EventType {
        EventType::from_repr((index % (EventType::COUNT - 1)) as u8).unwrap()
    }

    pub(crate) fn storage_class(index: usize) -> StorageClass {
        StorageClass::from_repr((index % StorageClass::COUNT) as u8).unwrap()
    }
}
