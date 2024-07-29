//! The regex rule.
//!

use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize, Serialize, PartialEq, Eq)]
pub struct Regex {
    regex: RegexWrapper,
}

impl Regex {
    /// Create a new regex rule.
    pub fn new(regex: regex::Regex) -> Self {
        Self {
            regex: RegexWrapper(regex),
        }
    }
}

#[derive(Debug, Deserialize, Serialize)]
pub struct RegexWrapper(#[serde(with = "serde_regex")] regex::Regex);

impl PartialEq for RegexWrapper {
    fn eq(&self, other: &Self) -> bool {
        self.0.as_str().eq(other.0.as_str())
    }
}

impl Eq for RegexWrapper {}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;
    use serde_json::{from_value, to_value};

    #[test]
    fn deserialize_regex() {
        let rule = json!({ "regex": "$(.*)+" });
        let result: Regex = from_value(rule).unwrap();
        assert_eq!(result, Regex::new(regex::Regex::new("$(.*)+").unwrap()));
    }

    #[test]
    fn serialize_regex() {
        let result = to_value(Regex::new(regex::Regex::new("$(.*)+").unwrap())).unwrap();
        assert_eq!(result, json!({ "regex": "$(.*)+" }));
    }
}
