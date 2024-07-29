//! The prefix rule.
//!

use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize, Serialize, Default, PartialEq, Eq)]
pub struct Prefix {
    prefix: String,
}

impl Prefix {
    pub fn new(prefix: String) -> Self {
        Self { prefix }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;
    use serde_json::{from_value, to_value};

    #[test]
    fn deserialize_prefix() {
        let rule = json!({ "prefix": "prefix" });
        let result: Prefix = from_value(rule).unwrap();
        assert_eq!(result, Prefix::new("prefix".to_string()));
    }

    #[test]
    fn serialize_prefix() {
        let result = to_value(Prefix::new("prefix".to_string())).unwrap();
        assert_eq!(result, json!({ "prefix": "prefix" }));
    }
}
