//! The suffix rule.
//!

use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize, Serialize, Default, PartialEq, Eq)]
pub struct Suffix {
    suffix: String,
}

impl Suffix {
    /// Create a new suffix rule.
    pub fn new(suffix: String) -> Self {
        Self { suffix }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;
    use serde_json::{from_value, to_value};

    #[test]
    fn deserialize_suffix() {
        let rule = json!({ "suffix": "suffix" });
        let result: Suffix = from_value(rule).unwrap();
        assert_eq!(result, Suffix::new("suffix".to_string()));
    }

    #[test]
    fn serialize_suffix() {
        let result = to_value(Suffix::new("suffix".to_string())).unwrap();
        assert_eq!(result, json!({ "suffix": "suffix" }));
    }
}
