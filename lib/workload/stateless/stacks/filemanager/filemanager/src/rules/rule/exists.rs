//! The exists rule.
//!

use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize, Serialize, Default, PartialEq, Eq)]
pub struct Exists {
    exists: bool,
}

impl Exists {
    /// Create a new exists rule.
    pub fn new(exists: bool) -> Self {
        Self { exists }
    }
}

#[cfg(test)]
mod tests {
    use serde_json::json;
    use serde_json::{from_value, to_value};

    use super::*;

    #[test]
    fn deserialize_exists() {
        let rule = json!({ "exists": true });
        let result: Exists = from_value(rule).unwrap();
        assert_eq!(result, Exists::new(true));
    }

    #[test]
    fn serialize_exists() {
        let result = to_value(Exists::new(false)).unwrap();
        assert_eq!(result, json!({ "exists": false }));
    }
}
