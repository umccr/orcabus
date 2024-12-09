//! Logic related to extracting query parameters for filters.
//!

use std::collections::HashSet;
use aws_lambda_events::http::StatusCode;
use axum::extract::FromRequestParts;
use axum::http::request::Parts;
use axum::http::uri::PathAndQuery;
use axum::http::Uri;
use percent_encoding::percent_decode_str;
use serde::de::DeserializeOwned;
use serde_qs::axum::QsQueryRejection;
use std::str::FromStr;

/// Configuration for the extractor. Allows omitting certain keys from the extraction
/// logic.
#[derive(Debug)]
pub struct QsQueryConfig {
    omit: HashSet<String>,
}

/// An extractor which allows parsing multiple named nested keys without an extra
/// `[]`. Normally to specify multiple nested keys, a `[]`. For example, `key[a][]=123&key[a][]=456`
/// works but `key[a]=123&key[a]=456` does not. This extract allow the latter example to work
/// by transforming it into the former.
#[derive(Debug)]
pub struct QsQuery<T>(pub T, QsQueryConfig);

#[axum::async_trait]
impl<T, S> FromRequestParts<S> for QsQuery<T>
where
    T: DeserializeOwned,
    S: Send + Sync,
{
    type Rejection = QsQueryRejection;

    async fn from_request_parts(parts: &mut Parts, state: &S) -> Result<Self, Self::Rejection> {
        let query = percent_decode_str(parts.uri.query().unwrap_or_default())
            .decode_utf8()
            .map_err(|err| QsQueryRejection::new(err, StatusCode::BAD_REQUEST))?;

        let mut output_qs = parts.uri.path().to_string() + "?";
        output_qs.reserve(query.len());

        let mut queries = query.split('&').peekable();
        // For each individual query.
        while let Some(query) = queries.next() {
            let mut iterator = query.chars().peekable();
            let mut after_equals = false;
            // Iterate over each character.
            while let Some(char) = iterator.next() {
                // Always copy the existing query character.
                output_qs.push(char);

                // Everything after '=' should not be transformed.
                if char == '=' {
                    after_equals = true;
                }
                if after_equals {
                    continue;
                }

                // Anything that takes the form of [*] should be transformed.
                if char == '[' {
                    let mut chars_between_brackets = 0;
                    for char in iterator.by_ref() {
                        // Still copy existing characters.
                        output_qs.push(char);
                        if char == ']' {
                            break;
                        }
                        chars_between_brackets += 1;
                    }

                    // Only transform if there is at least one character between the brackets.
                    // This will not trigger if the querystring already contains "[]".
                    if chars_between_brackets >= 1 && iterator.peek() != Some(&'[') {
                        output_qs.push_str("[]");
                    }
                }
            }

            // Add back the '&'
            if queries.peek().is_some() {
                output_qs.push('&');
            }
        }

        let path_and_query = PathAndQuery::from_str(&output_qs)
            .map_err(|err| QsQueryRejection::new(err, StatusCode::BAD_REQUEST))?;
        let mut uri = parts.clone().uri.into_parts();
        uri.path_and_query = Some(path_and_query);
        parts.uri = Uri::from_parts(uri)
            .map_err(|err| QsQueryRejection::new(err, StatusCode::BAD_REQUEST))?;

        let serde_qs::axum::QsQuery(qs) =
            serde_qs::axum::QsQuery::<T>::from_request_parts(parts, state).await?;
        Ok(Self(qs))
    }
}

#[cfg(test)]
pub(crate) mod tests {
    use super::*;
    use axum::http;
    use percent_encoding::{percent_encode, NON_ALPHANUMERIC};
    use serde_json::json;
    use serde_json::Value;
    use std::collections::HashMap;

    #[tokio::test]
    async fn extract() {
        let result: HashMap<String, Value> = get_result("/?key[a]=123&key[a]=456").await;
        assert_eq!(
            result,
            HashMap::from_iter(vec![("key".to_string(), json!({"a": ["123", "456"]}))])
        );
    }

    #[tokio::test]
    async fn extract_percent_encoded() {
        let query =
            percent_encode("key[a]=123&key[a]=456".as_bytes(), NON_ALPHANUMERIC).to_string();
        let result: HashMap<String, Value> = get_result(&format!("/?{query}")).await;
        assert_eq!(
            result,
            HashMap::from_iter(vec![("key".to_string(), json!({"a": ["123", "456"]}))])
        );
    }

    #[tokio::test]
    async fn extract_mixed() {
        let result: HashMap<String, Value> = get_result("/?key[a][]=123&key[a]=456").await;
        assert_eq!(
            result,
            HashMap::from_iter(vec![("key".to_string(), json!({"a": ["123", "456"]}))])
        );
    }

    #[tokio::test]
    async fn extract_sequence() {
        let result: HashMap<String, Value> = get_result("/?key[]=123&key[]=456").await;
        assert_eq!(
            result,
            HashMap::from_iter(vec![("key".to_string(), json!(["123", "456"]))])
        );
    }

    #[tokio::test]
    async fn extract_brackets_after_equals() {
        let result: HashMap<String, Value> = get_result("/?key[a]=1[2]3&key[a]=4[5]6").await;
        assert_eq!(
            result,
            HashMap::from_iter(vec![("key".to_string(), json!({"a": ["1[2]3", "4[5]6"]}))])
        );
    }

    pub(crate) async fn get_result<T>(request: &str) -> T
    where
        T: DeserializeOwned,
    {
        let request = http::Request::builder().uri(request).body(()).unwrap();

        QsQuery::<T>::from_request_parts(&mut request.into_parts().0, &())
            .await
            .unwrap()
            .0
    }
}
