use crate::rules::rule::numeric::operation::Operation;
use serde::de::{SeqAccess, Visitor};
use serde::ser::SerializeSeq;
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use std::fmt;
use std::marker::PhantomData;

pub mod operation;

#[derive(Debug, Deserialize, Serialize, Default, PartialEq)]
pub struct Numeric {
    #[serde(serialize_with = "serialize", deserialize_with = "deserialize")]
    numeric: Vec<(Operation, f64)>,
}

impl Numeric {
    /// Create a new numeric rule.
    pub fn new(numeric: Vec<(Operation, f64)>) -> Self {
        Self { numeric }
    }
}

/// Serialize keys and values into a flat sequence. Based on
/// https://github.com/serde-rs/serde/issues/1378#issuecomment-419657606.
pub fn serialize<K, V, S>(pairs: &[(K, V)], serializer: S) -> Result<S::Ok, S::Error>
where
    K: Serialize,
    V: Serialize,
    S: Serializer,
{
    let mut seq = serializer.serialize_seq(Some(pairs.len()))?;
    for (key, value) in pairs {
        seq.serialize_element(key)?;
        seq.serialize_element(value)?;
    }
    seq.end()
}

/// Deserialize pairs of keys and values from a sequence. Based on
/// https://github.com/serde-rs/serde/issues/1378#issuecomment-419657606.
pub fn deserialize<'de, K, V, D>(deserializer: D) -> Result<Vec<(K, V)>, D::Error>
where
    K: Deserialize<'de>,
    V: Deserialize<'de>,
    D: Deserializer<'de>,
{
    struct PairsVisitor<K, V> {
        key: PhantomData<K>,
        value: PhantomData<V>,
    }

    impl<'de, K, V> Visitor<'de> for PairsVisitor<K, V>
    where
        K: Deserialize<'de>,
        V: Deserialize<'de>,
    {
        type Value = Vec<(K, V)>;

        fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
            formatter.write_str("pairs of keys and values as a sequence")
        }

        fn visit_seq<A>(self, mut seq: A) -> Result<Self::Value, A::Error>
        where
            A: SeqAccess<'de>,
        {
            let mut vec = Vec::new();
            while let (Some(key), Some(value)) = (seq.next_element()?, seq.next_element()?) {
                vec.push((key, value));
            }
            Ok(vec)
        }
    }

    deserializer.deserialize_seq(PairsVisitor {
        key: PhantomData::<K>,
        value: PhantomData::<V>,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;
    use serde_json::{from_value, to_value};

    #[test]
    fn deserialize_numeric() {
        let rule = json!({ "numeric": [">", 1, "<=", 5] });
        let result: Numeric = from_value(rule).unwrap();
        assert_eq!(
            result,
            Numeric::new(vec![
                (Operation::GreaterThan, 1.0),
                (Operation::LessThanOrEqual, 5.0)
            ])
        );

        let rule = json!({ "numeric": ["<", 10, ">=", 5] });
        let result: Numeric = from_value(rule).unwrap();
        assert_eq!(
            result,
            Numeric::new(vec![
                (Operation::LessThan, 10.0),
                (Operation::GreaterThanOrEqual, 5.0)
            ])
        );

        let rule = json!({ "numeric": ["=", 5] });
        let result: Numeric = from_value(rule).unwrap();
        assert_eq!(result, Numeric::new(vec![(Operation::Equals, 5.0)]));
    }

    #[test]
    fn serialize_numeric() {
        let value = Numeric::new(vec![
            (Operation::GreaterThan, 1.0),
            (Operation::LessThanOrEqual, 5.0),
        ]);
        let result = to_value(value).unwrap();
        assert_eq!(result, json!({ "numeric": [">", 1.0, "<=", 5.0] }));

        let value = Numeric::new(vec![
            (Operation::LessThan, 10.0),
            (Operation::GreaterThanOrEqual, 5.0),
        ]);
        let result = to_value(value).unwrap();
        assert_eq!(result, json!({ "numeric": ["<", 10.0, ">=", 5.0] }));

        let value = Numeric::new(vec![(Operation::Equals, 5.0)]);
        let result = to_value(value).unwrap();
        assert_eq!(result, json!({ "numeric": ["=", 5.0] }));
    }
}
