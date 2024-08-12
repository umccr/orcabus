//! This module handles all logic related to querying the file manager through APIs/events.
//!

use std::ops::Add;

use chrono::{DateTime, Days};
use rand::seq::SliceRandom;
use rand::thread_rng;
use sea_orm::Set;
use sea_orm::{ActiveModelTrait, TryIntoModel};
use serde_json::json;
use strum::EnumCount;

use crate::database::entities::s3_object::ActiveModel as ActiveS3Object;
use crate::database::entities::s3_object::Model as S3Object;
use crate::database::entities::sea_orm_active_enums::{EventType, StorageClass};
use crate::database::Client;
use crate::uuid::UuidGenerator;

pub mod get;
pub mod list;
pub mod update;

/// Container for generating database entries.
#[derive(Debug)]
pub struct Entries {
    pub s3_objects: Vec<S3Object>,
}

impl From<Vec<S3Object>> for Entries {
    fn from(s3_objects: Vec<S3Object>) -> Self {
        Self { s3_objects }
    }
}

impl Entries {
    /// Create an entries tuple from the arguments.
    pub async fn initialize_database(
        client: &Client,
        n: usize,
        shuffle: bool,
        bucket_divisor: usize,
        key_divisor: usize,
    ) -> Vec<S3Object> {
        let mut output = vec![];

        let mut entries: Vec<_> = (0..n)
            .map(|index| Self::generate_entry(index, bucket_divisor, key_divisor))
            .collect();

        if shuffle {
            entries.shuffle(&mut thread_rng());
        }

        for s3_object in entries {
            s3_object
                .clone()
                .insert(client.connection_ref())
                .await
                .unwrap();

            output.push(s3_object.try_into_model().unwrap());
        }

        output
    }

    /// Generate a single record entry using the index.
    pub fn generate_entry(
        index: usize,
        bucket_divisor: usize,
        key_divisor: usize,
    ) -> ActiveS3Object {
        let event = Self::event_type(index);
        let date = || Set(Some(DateTime::default().add(Days::new(index as u64))));
        let attributes = Some(json!({
            "attribute_id": format!("{}", index),
            "nested_id": {
                "attribute_id": format!("{}", index)
            }
        }));

        ActiveS3Object {
            s3_object_id: Set(UuidGenerator::generate()),
            event_type: Set(event.clone()),
            bucket: Set((index / bucket_divisor).to_string()),
            key: Set((index / key_divisor).to_string()),
            version_id: Set((index / key_divisor).to_string()),
            date: date(),
            size: Set(Some(index as i64)),
            sha256: Set(Some(index.to_string())),
            last_modified_date: date(),
            e_tag: Set(Some(index.to_string())),
            storage_class: Set(Some(Self::storage_class(index))),
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
        }
    }

    fn event_type(index: usize) -> EventType {
        EventType::from_repr((index % (EventType::COUNT - 1)) as u8).unwrap()
    }

    fn storage_class(index: usize) -> StorageClass {
        StorageClass::from_repr((index % StorageClass::COUNT) as u8).unwrap()
    }
}

/// Generate entries into the filemanager database.
#[derive(Debug)]
pub struct EntriesBuilder {
    n: usize,
    bucket_divisor: usize,
    key_divisor: usize,
    shuffle: bool,
}

impl EntriesBuilder {
    /// Set the number of entries.
    pub fn with_n(mut self, n: usize) -> Self {
        self.n = n;
        self
    }

    /// Set the bucket ratio.
    pub fn with_bucket_divisor(mut self, bucket_divisor: usize) -> Self {
        self.bucket_divisor = bucket_divisor;
        self
    }

    /// Set the key ratio.
    pub fn with_key_divisor(mut self, key_divisor: usize) -> Self {
        self.key_divisor = key_divisor;
        self
    }

    /// Set whether to shuffle.
    pub fn with_shuffle(mut self, shuffle: bool) -> Self {
        self.shuffle = shuffle;
        self
    }

    /// Build the entries and initialize the database.
    pub async fn build(self, client: &Client) -> Entries {
        let mut entries = Entries::initialize_database(
            client,
            self.n,
            self.shuffle,
            self.bucket_divisor,
            self.key_divisor,
        )
        .await;

        // Return the correct ordering for test purposes
        entries.sort_by(|a, b| a.sequencer.cmp(&b.sequencer));

        entries.into()
    }
}

impl Default for EntriesBuilder {
    fn default() -> Self {
        Self {
            n: 10,
            bucket_divisor: 2,
            key_divisor: 1,
            shuffle: false,
        }
    }
}
