//! Wildcard filtering logic.
//!

use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

use crate::error::Error::ParseError;
use crate::error::Result;

/// An enum which deserializes into a concrete type or a wildcard. This is used for better
/// type support when non-string filter parameters such as `StorageClass` or `EventType`.
#[derive(Serialize, Deserialize, Debug, Eq, PartialEq, Clone)]
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
#[derive(Serialize, Deserialize, Debug, Default, ToSchema, Eq, PartialEq, Clone)]
#[serde(default, rename_all = "camelCase")]
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

    fn wildcard_positions(&self) -> (Vec<usize>, Vec<usize>) {
        let mut chars = self.0.chars().enumerate().peekable();

        let mut wildcard_positions = vec![];
        let mut escaped_positions = vec![];
        while let Some((pos, char)) = chars.next() {
            // If there is a backslash, then the next character can be '*' and not be a wildcard.
            if char == '\\' {
                let peek = chars.peek();
                if let Some((_, next_char)) = peek {
                    if *next_char == '*' || *next_char == '?' || *next_char == '\\' {
                        // Skip the next character as we have just processed it.
                        chars.next();
                        escaped_positions.push(pos);
                        continue;
                    }
                }

                escaped_positions.push(pos);
            }

            // This will result in a wildcard match as it is not escaped.
            if char == '*' || char == '?' {
                wildcard_positions.push(pos);
            }
        }

        (wildcard_positions, escaped_positions)
    }

    fn to_postgres_wildcard(
        &self,
        escape_characters: &str,
        escape_replacement: &str,
        single_wildcard: &str,
        multi_wildcard: &str,
    ) -> Result<String> {
        let (mut wildcard_positions, mut escaped_positions) = self.wildcard_positions();
        let mut out = String::with_capacity(self.0.len());

        let mut chars = self.0.chars().enumerate().peekable();
        while let Some((pos, char)) = chars.next() {
            // A wildcard should be converted to a regex.
            if Some(&pos) == wildcard_positions.first() {
                // This is a wildcard.
                wildcard_positions.remove(0);
                if char == '?' {
                    out.push_str(single_wildcard);
                } else {
                    out.push_str(multi_wildcard);
                }

                continue;
            }

            // An escaped wildcard needs to be converted to an escaped regex character.
            if Some(&pos) == escaped_positions.first() {
                escaped_positions.remove(0);

                // The next character must be a valid escape.
                match chars.peek() {
                    Some((_, next_char))
                        if *next_char != '*' && *next_char != '?' && *next_char != '\\' =>
                    {
                        return Err(ParseError(format!(
                            "invalid escape character: `\\{}`",
                            next_char
                        )));
                    }
                    None => return Err(ParseError("invalid escape character".to_string())),
                    _ => {}
                }

                // Skip the escape, process on next iteration.
                continue;
            }

            if escape_characters.contains(char) {
                out.push_str(escape_replacement);
            }
            out.push(char);
        }

        Ok(out)
    }

    /// Find all wildcard positions contained in the underlying string and return true if there is a wildcard.
    /// This is useful to convert the wildcard to a postgres `like_regex` statement, because wildcards
    /// without any `*` don't need to be run through `like` and can instead be used in an equality
    /// comparison.
    pub fn contains_wildcard(&self) -> bool {
        !self.wildcard_positions().0.is_empty()
    }

    /// Convert this wildcard to a postgres jsonbpath `like_regex` string, escaping relevant characters.
    pub fn to_like_regex(&self) -> Result<String> {
        // Valid postgres regex characters need to be escaped.
        let escape_characters = r"!$()*+.:<=>?[\]^{|}-";
        // Two backslashes needed as this is part of a jsonbpath escape:
        // https://www.postgresql.org/docs/current/functions-json.html#JSONPATH-REGULAR-EXPRESSIONS
        let escape_replacement = r"\\";
        self.to_postgres_wildcard(escape_characters, escape_replacement, ".", ".*")
    }

    /// Convert this wildcard to a postgres `like` expression, escaping relevant characters.
    pub fn to_like_expression(&self) -> Result<String> {
        // Valid postgres regex characters need to be escaped.
        let escape_characters = r"\%_";
        // Only a single backslash is needed to escape the above characters.
        let escape_replacement = r"\";
        self.to_postgres_wildcard(escape_characters, escape_replacement, "_", "%")
    }

    /// Convert this wildcard to a postgres equality expression.
    pub fn to_eq_expression(&self) -> Result<String> {
        // Nothing to escape for equality except the escape character
        let escape_characters = r"\";
        let escape_replacement = r"\";
        self.to_postgres_wildcard(escape_characters, escape_replacement, "", "")
    }
}

#[cfg(test)]
mod tests {
    use sea_orm::prelude::DateTimeWithTimeZone;
    use serde_json::json;

    use crate::database::entities::sea_orm_active_enums::{EventType, StorageClass};

    use super::*;

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

        let wildcard: WildcardEither<EventType> = serde_json::from_value(json!("Create*")).unwrap();
        assert_eq!(
            wildcard,
            WildcardEither::Wildcard(Wildcard::new("Create*".to_string()))
        );
        let wildcard: WildcardEither<DateTimeWithTimeZone> =
            serde_json::from_value(json!("1970-01-01*")).unwrap();
        assert_eq!(
            wildcard,
            WildcardEither::Wildcard(Wildcard::new("1970-01-01*".to_string()))
        );
        let wildcard: WildcardEither<StorageClass> =
            serde_json::from_value(json!("Standar*")).unwrap();
        assert_eq!(
            wildcard,
            WildcardEither::Wildcard(Wildcard::new("Standar*".to_string()))
        );
    }

    #[test]
    fn contains_wildcard() {
        assert!(!Wildcard::new(r#"test"#.to_string()).contains_wildcard());
        assert!(!Wildcard::new(r#"tes\n"#.to_string()).contains_wildcard());

        assert!(Wildcard::new(r#"t*st"#.to_string()).contains_wildcard());
        assert!(Wildcard::new(r#"t?st"#.to_string()).contains_wildcard());

        assert!(!Wildcard::new(r#"t\*st"#.to_string()).contains_wildcard());
        assert!(!Wildcard::new(r#"t\?st"#.to_string()).contains_wildcard());
        assert!(!Wildcard::new(r#"t\\st"#.to_string()).contains_wildcard());

        assert!(Wildcard::new(r#"te**"#.to_string()).contains_wildcard());
        assert!(Wildcard::new(r#"te??"#.to_string()).contains_wildcard());
        assert!(!Wildcard::new(r#"te\\\\"#.to_string()).contains_wildcard());

        assert!(Wildcard::new(r#"te\**"#.to_string()).contains_wildcard());
        assert!(Wildcard::new(r#"te\??"#.to_string()).contains_wildcard());
        assert!(!Wildcard::new(r#"tes\\"#.to_string()).contains_wildcard());
    }

    #[test]
    fn to_like_expression() {
        assert_eq!(
            Wildcard::new(r#"test"#.to_string())
                .to_like_expression()
                .unwrap(),
            "test"
        );
        assert_eq!(
            Wildcard::new("tes\n".to_string())
                .to_like_expression()
                .unwrap(),
            "tes\n"
        );

        assert_eq!(
            Wildcard::new("t*st".to_string())
                .to_like_expression()
                .unwrap(),
            "t%st"
        );
        assert_eq!(
            Wildcard::new("t?st".to_string())
                .to_like_expression()
                .unwrap(),
            "t_st"
        );

        assert_eq!(
            Wildcard::new(r"t\*st".to_string())
                .to_like_expression()
                .unwrap(),
            r"t*st"
        );
        assert_eq!(
            Wildcard::new(r"t\?st".to_string())
                .to_like_expression()
                .unwrap(),
            r"t?st"
        );
        assert_eq!(
            Wildcard::new(r"t\\st".to_string())
                .to_like_expression()
                .unwrap(),
            r"t\\st"
        );

        assert_eq!(
            Wildcard::new(r"t%st".to_string())
                .to_like_expression()
                .unwrap(),
            r"t\%st"
        );
        assert_eq!(
            Wildcard::new(r"t_st".to_string())
                .to_like_expression()
                .unwrap(),
            r"t\_st"
        );

        assert!(Wildcard::new(r"t\st".to_string())
            .to_like_expression()
            .is_err());
        assert!(Wildcard::new(r"tes\".to_string())
            .to_like_expression()
            .is_err());
    }

    #[test]
    fn to_like_regex() {
        assert_eq!(
            Wildcard::new(r#"test"#.to_string())
                .to_like_regex()
                .unwrap(),
            "test"
        );
        assert_eq!(
            Wildcard::new("tes\n".to_string()).to_like_regex().unwrap(),
            "tes\n"
        );

        assert_eq!(
            Wildcard::new("t*st".to_string()).to_like_regex().unwrap(),
            "t.*st"
        );
        assert_eq!(
            Wildcard::new("t?st".to_string()).to_like_regex().unwrap(),
            "t.st"
        );

        assert_eq!(
            Wildcard::new(r"t\*st".to_string()).to_like_regex().unwrap(),
            r"t\\*st"
        );
        assert_eq!(
            Wildcard::new(r"t\?st".to_string()).to_like_regex().unwrap(),
            r"t\\?st"
        );
        assert_eq!(
            Wildcard::new(r"t\\st".to_string()).to_like_regex().unwrap(),
            r"t\\\st"
        );

        assert_eq!(
            Wildcard::new(r"t.st".to_string()).to_like_regex().unwrap(),
            r"t\\.st"
        );
        assert_eq!(
            Wildcard::new(r"t-st".to_string()).to_like_regex().unwrap(),
            r"t\\-st"
        );

        assert!(Wildcard::new(r"t\st".to_string()).to_like_regex().is_err());
        assert!(Wildcard::new(r"tes\".to_string()).to_like_regex().is_err());
    }

    #[test]
    fn to_eq_expression() {
        assert_eq!(
            Wildcard::new(r#"test"#.to_string())
                .to_eq_expression()
                .unwrap(),
            "test"
        );
        assert_eq!(
            Wildcard::new("tes\n".to_string())
                .to_eq_expression()
                .unwrap(),
            "tes\n"
        );

        assert_eq!(
            Wildcard::new(r"t\*st".to_string())
                .to_eq_expression()
                .unwrap(),
            "t*st"
        );
        assert_eq!(
            Wildcard::new(r"t\?st".to_string())
                .to_eq_expression()
                .unwrap(),
            "t?st"
        );

        assert_eq!(
            Wildcard::new(r"t.st".to_string())
                .to_eq_expression()
                .unwrap(),
            r"t.st"
        );
        assert_eq!(
            Wildcard::new(r"t%st".to_string())
                .to_eq_expression()
                .unwrap(),
            r"t%st"
        );
        assert_eq!(
            Wildcard::new(r"t\\st".to_string())
                .to_eq_expression()
                .unwrap(),
            r"t\\st"
        );

        assert!(Wildcard::new(r"t\st".to_string())
            .to_eq_expression()
            .is_err());
        assert!(Wildcard::new(r"tes\".to_string())
            .to_eq_expression()
            .is_err());
    }
}
