//! This module handles all logic related to querying the file manager through APIs/events.
//!

pub mod get;
pub mod list;

#[cfg(test)]
pub(crate) mod tests {
    use std::ops::Add;

    use chrono::{DateTime, Days};
    use sea_orm::Set;
    use sea_orm::{ActiveModelTrait, TryIntoModel};
    use strum::EnumCount;

    use crate::database::entities::object::ActiveModel as ActiveObject;
    use crate::database::entities::object::Model as Object;
    use crate::database::entities::s3_object::ActiveModel as ActiveS3Object;
    use crate::database::entities::s3_object::Model as S3Object;
    use crate::database::entities::sea_orm_active_enums::{EventType, StorageClass};
    use crate::database::Client;
    use crate::uuid::UuidGenerator;

    /// Initialize database state for testing.
    pub(crate) async fn initialize_database(client: &Client, n: usize) -> Vec<(Object, S3Object)> {
        let mut output = vec![];

        for index in 0..n {
            let (object, s3_object) = generate_entry(index);

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

    pub(crate) fn generate_entry(index: usize) -> (ActiveObject, ActiveS3Object) {
        let object_id = UuidGenerator::generate();
        let event = event_type(index);
        let date = || Set(Some(DateTime::default().add(Days::new(index as u64))));

        (
            ActiveObject {
                object_id: Set(object_id),
                attributes: Set(None),
            },
            ActiveS3Object {
                s3_object_id: Set(UuidGenerator::generate()),
                object_id: Set(object_id),
                public_id: Set(UuidGenerator::generate()),
                event_type: Set(event.clone()),
                // Half as many buckets as keys.
                bucket: Set((index / 2).to_string()),
                key: Set(index.to_string()),
                version_id: Set(index.to_string()),
                date: date(),
                size: Set(Some(index as i64)),
                sha256: Set(Some(index.to_string())),
                last_modified_date: date(),
                e_tag: Set(Some(index.to_string())),
                storage_class: Set(Some(storage_class(index))),
                sequencer: Set(Some(index.to_string())),
                is_delete_marker: Set(false),
                number_duplicate_events: Set(0),
                attributes: Set(None),
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
