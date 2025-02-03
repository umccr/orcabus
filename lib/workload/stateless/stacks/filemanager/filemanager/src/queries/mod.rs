//! This module handles all logic related to querying the file manager through APIs/events.
//!

use std::collections::HashMap;
use std::ops::Add;

use crate::database::aws::ingester::Ingester;
use crate::database::entities::s3_object::ActiveModel as ActiveS3Object;
use crate::database::entities::s3_object::Model as S3Object;
use crate::database::entities::sea_orm_active_enums::{EventType, Reason, StorageClass};
use crate::database::Client;
use crate::error::Result;
use crate::events::aws;
use crate::events::aws::{message, FlatS3EventMessage, FlatS3EventMessages};
use crate::uuid::UuidGenerator;
use chrono::{DateTime, Days};
use rand::seq::SliceRandom;
use rand::thread_rng;
use sea_orm::Set;
use sea_orm::TryIntoModel;
use serde_json::json;
use strum::EnumCount;
use uuid::Uuid;

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
        builder: EntriesBuilder,
    ) -> Result<Vec<S3Object>> {
        let mut output = vec![];

        let mut entries: Vec<(_, _)> = (0..builder.n)
            .map(|index| {
                let uuid = UuidGenerator::generate();
                let ingest_id = builder.ingest_id.unwrap_or_else(UuidGenerator::generate);
                (
                    Self::generate_entry(
                        index,
                        (builder.bucket_divisor, builder.key_divisor),
                        ingest_id,
                        uuid,
                        builder.values.get(&index).map(|k| k.to_string()),
                        builder.prefixes.get(&index).map(|k| k.as_str()),
                        builder.suffixes.get(&index).map(|k| k.as_str()),
                    ),
                    Self::generate_event_message(
                        index,
                        (builder.bucket_divisor, builder.key_divisor),
                        ingest_id,
                        uuid,
                        builder.values.get(&index).map(|k| k.to_string()),
                        builder.prefixes.get(&index).map(|k| k.as_str()),
                        builder.suffixes.get(&index).map(|k| k.as_str()),
                    ),
                )
            })
            .collect();

        if builder.shuffle {
            entries.shuffle(&mut thread_rng());
        }

        for (s3_object, message) in entries {
            Ingester::new(client.clone())
                .ingest_events(FlatS3EventMessages(vec![message]).into())
                .await?;

            output.push(s3_object.try_into_model()?);
        }

        Ok(output)
    }

    /// Generate a single record entry using the index.
    pub fn generate_entry(
        index: usize,
        divisors: (usize, usize),
        ingest_id: Uuid,
        uuid: Uuid,
        key: Option<String>,
        prefix: Option<&str>,
        suffix: Option<&str>,
    ) -> ActiveS3Object {
        let event =
            EventType::from_repr(index % (EventType::COUNT - 1)).unwrap_or(EventType::Created);
        let date = || Set(Some(DateTime::default().add(Days::new(index as u64))));
        let attributes = Some(json!({
            "attributeId": format!("{}", index),
            "nestedId": {
                "attributeId": format!("{}", index)
            }
        }));

        ActiveS3Object {
            s3_object_id: Set(uuid),
            ingest_id: Set(Some(ingest_id)),
            event_type: Set(event.clone()),
            bucket: Set((index / divisors.0).to_string()),
            key: Set(prefix.unwrap_or_default().to_string()
                + &key.unwrap_or_else(|| (index / divisors.1).to_string())
                + suffix.unwrap_or_default()),
            version_id: Set((index / divisors.1).to_string()),
            event_time: date(),
            size: Set(Some(index as i64)),
            sha256: Set(Some(index.to_string())),
            last_modified_date: date(),
            e_tag: Set(Some(index.to_string())),
            storage_class: Set(StorageClass::from_repr(index % StorageClass::COUNT)),
            sequencer: Set(Some(index.to_string())),
            is_delete_marker: Set(false),
            is_current_state: Set(event == EventType::Created),
            number_duplicate_events: Set(0),
            attributes: Set(attributes),
            deleted_date: Set(None),
            deleted_sequencer: Set(None),
            number_reordered: Set(0),
            reason: Set(Reason::Unknown),
        }
    }

    /// Generate a single record event message.
    pub fn generate_event_message(
        index: usize,
        divisors: (usize, usize),
        ingest_id: Uuid,
        uuid: Uuid,
        key: Option<String>,
        prefix: Option<&str>,
        suffix: Option<&str>,
    ) -> FlatS3EventMessage {
        let event = message::EventType::from_repr(index % (EventType::COUNT - 1))
            .unwrap_or(message::EventType::Created);
        let date = || Some(DateTime::default().add(Days::new(index as u64)));
        let attributes = Some(json!({
            "attributeId": format!("{}", index),
            "nestedId": {
                "attributeId": format!("{}", index)
            }
        }));

        FlatS3EventMessage {
            s3_object_id: uuid,
            sequencer: Some(index.to_string()),
            bucket: (index / divisors.0).to_string(),
            key: prefix.unwrap_or_default().to_string()
                + &key.unwrap_or_else(|| (index / divisors.1).to_string())
                + suffix.unwrap_or_default(),
            version_id: (index / divisors.1).to_string(),
            size: Some(index as i64),
            e_tag: Some(index.to_string()),
            sha256: Some(index.to_string()),
            storage_class: aws::StorageClass::from_repr(index % StorageClass::COUNT),
            last_modified_date: date(),
            event_time: date(),
            is_current_state: event == message::EventType::Created,
            event_type: event,
            is_delete_marker: false,
            ingest_id: Some(ingest_id),
            reason: Reason::Unknown,
            attributes,
            number_duplicate_events: 0,
            number_reordered: 0,
        }
    }
}

/// Generate entries into the filemanager database.
#[derive(Debug)]
pub struct EntriesBuilder {
    pub(crate) n: usize,
    pub(crate) bucket_divisor: usize,
    pub(crate) key_divisor: usize,
    pub(crate) shuffle: bool,
    pub(crate) ingest_id: Option<Uuid>,
    pub(crate) values: HashMap<usize, String>,
    pub(crate) prefixes: HashMap<usize, String>,
    pub(crate) suffixes: HashMap<usize, String>,
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

    /// Set whether to shuffle.
    pub fn with_ingest_id(mut self, ingest_id: Uuid) -> Self {
        self.ingest_id = Some(ingest_id);
        self
    }

    /// Set the prefixes on some keys.
    pub fn with_prefixes(mut self, prefixes: HashMap<usize, String>) -> Self {
        self.prefixes = prefixes;
        self
    }

    /// Set the suffixes on some keys.
    pub fn with_suffixes(mut self, suffixes: HashMap<usize, String>) -> Self {
        self.suffixes = suffixes;
        self
    }

    /// Set the value of some keys.
    pub fn with_keys(mut self, keys: HashMap<usize, String>) -> Self {
        self.values = keys;
        self
    }

    /// Build the entries and initialize the database.
    pub async fn build(self, client: &Client) -> Result<Entries> {
        let mut entries = Entries::initialize_database(client, self).await?;

        // Return the correct ordering for test purposes
        entries.sort_by(|a, b| a.sequencer.cmp(&b.sequencer));

        Ok(entries.into())
    }
}

impl Default for EntriesBuilder {
    fn default() -> Self {
        Self {
            n: 10,
            bucket_divisor: 2,
            key_divisor: 1,
            shuffle: false,
            ingest_id: None,
            values: Default::default(),
            prefixes: Default::default(),
            suffixes: Default::default(),
        }
    }
}
