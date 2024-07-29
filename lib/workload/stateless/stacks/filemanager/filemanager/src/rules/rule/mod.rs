//! A rule is a JSON object of arrays which match particular filemanager events,
//! similar to AWS Event Ruler: https://github.com/aws/event-ruler
//!

use crate::rules::rule::exists::Exists;
use crate::rules::rule::numeric::Numeric;
use crate::rules::rule::prefix::Prefix;
use crate::rules::rule::regex::Regex;
use crate::rules::rule::suffix::Suffix;
use serde::{Deserialize, Serialize};

pub mod exists;
pub mod numeric;
pub mod prefix;
pub mod regex;
pub mod suffix;

#[derive(Debug, Deserialize, Serialize, Default, PartialEq)]
#[serde(default)]
pub struct EventRule {
    bucket: Vec<Rule>,
    key: Vec<Rule>,
    version_id: Vec<Rule>,
    size: Vec<Rule>,
    e_tag: Vec<Rule>,
    sha256: Vec<Rule>,
    storage_class: Vec<Rule>,
    event_type: Vec<Rule>,
    is_delete_marker: Vec<Rule>,
}

impl EventRule {
    /// Set the bucket.
    pub fn with_bucket(mut self, bucket: Vec<Rule>) -> Self {
        self.bucket = bucket;
        self
    }

    /// Set the key.
    pub fn with_key(mut self, key: Vec<Rule>) -> Self {
        self.key = key;
        self
    }

    /// Set the version_id.
    pub fn with_version_id(mut self, version_id: Vec<Rule>) -> Self {
        self.version_id = version_id;
        self
    }

    /// Set the size.
    pub fn with_size(mut self, size: Vec<Rule>) -> Self {
        self.size = size;
        self
    }

    /// Set the e_tag.
    pub fn with_e_tag(mut self, e_tag: Vec<Rule>) -> Self {
        self.e_tag = e_tag;
        self
    }

    /// Set the sha256.
    pub fn with_sha256(mut self, sha256: Vec<Rule>) -> Self {
        self.sha256 = sha256;
        self
    }

    /// Set the storage_class.
    pub fn with_storage_class(mut self, storage_class: Vec<Rule>) -> Self {
        self.storage_class = storage_class;
        self
    }

    /// Set the event_type.
    pub fn with_event_type(mut self, event_type: Vec<Rule>) -> Self {
        self.event_type = event_type;
        self
    }

    /// Set the is_delete_marker.
    pub fn with_is_delete_marker(mut self, is_delete_marker: Vec<Rule>) -> Self {
        self.is_delete_marker = is_delete_marker;
        self
    }
}

#[derive(Debug, Deserialize, Serialize, PartialEq)]
#[serde(untagged)]
pub enum Rule {
    DirectMatch(String),
    Prefix(Prefix),
    Suffix(Suffix),
    Regex(Regex),
    Exists(Exists),
    Numeric(Numeric),
}

#[cfg(test)]
mod tests {
    use serde_json::from_value;
    use serde_json::json;

    use super::*;

    #[test]
    fn deserialize_direct() {
        let rule = json!({
            "bucket": [ "bucket1", "bucket2" ],
        });
        let result: EventRule = from_value(rule).unwrap();
        assert_eq!(
            result,
            EventRule::default().with_bucket(vec![
                Rule::DirectMatch("bucket1".to_string()),
                Rule::DirectMatch("bucket2".to_string()),
            ])
        );
    }
}
