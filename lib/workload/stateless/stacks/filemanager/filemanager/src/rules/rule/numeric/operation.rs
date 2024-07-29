use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize, Serialize, Default, PartialEq, Eq)]
pub enum Operation {
    #[default]
    #[serde(rename = "=")]
    Equals,
    #[serde(rename = "<")]
    LessThan,
    #[serde(rename = "<=")]
    LessThanOrEqual,
    #[serde(rename = ">")]
    GreaterThan,
    #[serde(rename = ">=")]
    GreaterThanOrEqual,
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;
    use serde_json::{from_value, to_value};

    #[test]
    fn deserialize_operation() {
        let value = json!("=");
        let result: Operation = from_value(value).unwrap();
        assert_eq!(result, Operation::Equals);

        let value = json!("<");
        let result: Operation = from_value(value).unwrap();
        assert_eq!(result, Operation::LessThan);

        let value = json!("<=");
        let result: Operation = from_value(value).unwrap();
        assert_eq!(result, Operation::LessThanOrEqual);

        let value = json!(">");
        let result: Operation = from_value(value).unwrap();
        assert_eq!(result, Operation::GreaterThan);

        let value = json!(">=");
        let result: Operation = from_value(value).unwrap();
        assert_eq!(result, Operation::GreaterThanOrEqual);
    }

    #[test]
    fn serialize_operation() {
        let result = to_value(Operation::Equals).unwrap();
        assert_eq!(result, json!("="));

        let result = to_value(Operation::LessThan).unwrap();
        assert_eq!(result, json!("<"));

        let result = to_value(Operation::LessThanOrEqual).unwrap();
        assert_eq!(result, json!("<="));

        let result = to_value(Operation::GreaterThan).unwrap();
        assert_eq!(result, json!(">"));

        let result = to_value(Operation::GreaterThanOrEqual).unwrap();
        assert_eq!(result, json!(">="));
    }
}
