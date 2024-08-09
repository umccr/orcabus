//! Wildcard filtering logic.
//!

use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

/// An enum which deserializes into a concrete type or a wildcard. This is used for better
/// type support when non-string filter parameters such as `StorageClass` or `EventType`.
#[derive(Serialize, Deserialize, Debug, Eq, PartialEq)]
#[serde(untagged)]
pub enum WildcardEither<T> {
    Or(T),
    Wildcard(Wildcard),
}

impl<T> WildcardEither<T> {
    /// Create an or variant.
    pub fn or(value: T) -> WildcardEither<T> {
        Self::Or(value)
    }

    /// Create a wildcard variant.
    pub fn wildcard(wildcard: String) -> WildcardEither<T> {
        Self::Wildcard(Wildcard::new(wildcard))
    }

    /// Map the function to the type if this is an `Or` variant.
    pub fn map<F, U>(self, f: F) -> WildcardEither<U>
    where
        F: FnOnce(T) -> U,
    {
        match self {
            Self::Or(or) => WildcardEither::Or(f(or)),
            Self::Wildcard(wildcard) => WildcardEither::Wildcard(wildcard),
        }
    }
}

/// A wildcard type represents a filter to match arbitrary characters. Use '%' for multiple characters
/// and '_' for a single character. Use '\\' to escape these characters. Wildcards are converted to
/// postgres `like` or `ilike` queries.
#[derive(Serialize, Deserialize, Debug, Default, ToSchema, Eq, PartialEq)]
#[serde(default)]
pub struct Wildcard(pub(crate) String);

impl Wildcard {
    /// Create a new wildcard.
    pub fn new(wildcard: String) -> Self {
        Self(wildcard)
    }

    /// Get the inner string value.
    pub fn into_inner(self) -> String {
        self.0
    }

    /// Check whether there are wildcard matches contained in this wildcard. This is useful to
    /// convert the wildcard to a postgres `like` statement, because wildcards without any
    /// `%` or `_` don't need to be run through `like` and can instead be used in an equality
    /// comparison
    pub fn contains_wildcard(&self) -> bool {
        let mut chars = self.0.chars().peekable();

        while let Some(char) = chars.next() {
            // If there is a backslash, then the next character can be either '%' or '_' and not
            // pass this check.
            if char == '\\' {
                let peek = chars.peek();
                if let Some(next_char) = peek {
                    if *next_char == '%' || *next_char == '_' {
                        // Skip the next character as we have just processed it.
                        chars.next();
                        continue;
                    }
                }
            }

            // This will result in a wildcard match as it is not escaped.
            if char == '%' || char == '_' {
                return true;
            }
        }

        false
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::database::entities::sea_orm_active_enums::{EventType, StorageClass};
    use sea_orm::prelude::DateTimeWithTimeZone;
    use serde_json::json;

    #[test]
    fn deserialize_wildcard_either() {
        let wildcard: WildcardEither<EventType> = serde_json::from_value(json!("Created")).unwrap();
        assert_eq!(wildcard, WildcardEither::Or(EventType::Created));
        let wildcard: WildcardEither<DateTimeWithTimeZone> =
            serde_json::from_value(json!("1970-01-01T00:00:00.000Z")).unwrap();
        assert_eq!(
            wildcard,
            WildcardEither::Or(DateTimeWithTimeZone::default())
        );
        let wildcard: WildcardEither<StorageClass> =
            serde_json::from_value(json!("Standard")).unwrap();
        assert_eq!(wildcard, WildcardEither::Or(StorageClass::Standard));

        let wildcard: WildcardEither<EventType> = serde_json::from_value(json!("Create%")).unwrap();
        assert_eq!(
            wildcard,
            WildcardEither::Wildcard(Wildcard::new("Create%".to_string()))
        );
        let wildcard: WildcardEither<DateTimeWithTimeZone> =
            serde_json::from_value(json!("1970-01-01%")).unwrap();
        assert_eq!(
            wildcard,
            WildcardEither::Wildcard(Wildcard::new("1970-01-01%".to_string()))
        );
        let wildcard: WildcardEither<StorageClass> =
            serde_json::from_value(json!("Standar%")).unwrap();
        assert_eq!(
            wildcard,
            WildcardEither::Wildcard(Wildcard::new("Standar%".to_string()))
        );
    }

    #[test]
    fn wildcard_deserialize() {
        assert!(!Wildcard::new(r#"test"#.to_string()).contains_wildcard());
        assert!(!Wildcard::new(r#"tes\n"#.to_string()).contains_wildcard());

        assert!(Wildcard::new(r#"t%st"#.to_string()).contains_wildcard());
        assert!(Wildcard::new(r#"t_st"#.to_string()).contains_wildcard());

        assert!(!Wildcard::new(r#"t\%st"#.to_string()).contains_wildcard());
        assert!(!Wildcard::new(r#"t\_st"#.to_string()).contains_wildcard());
        assert!(!Wildcard::new(r#"t\\st"#.to_string()).contains_wildcard());

        assert!(Wildcard::new(r#"te%%"#.to_string()).contains_wildcard());
        assert!(Wildcard::new(r#"te__"#.to_string()).contains_wildcard());
        assert!(!Wildcard::new(r#"te\\\\"#.to_string()).contains_wildcard());

        assert!(Wildcard::new(r#"te\%%"#.to_string()).contains_wildcard());
        assert!(Wildcard::new(r#"te\__"#.to_string()).contains_wildcard());
        assert!(!Wildcard::new(r#"tes\\"#.to_string()).contains_wildcard());
    }
}
