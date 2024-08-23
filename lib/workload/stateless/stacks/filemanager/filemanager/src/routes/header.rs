//! Functions related to parsing header information.
//!

use axum::http::header::AsHeaderName;
use axum::http::HeaderMap;

use crate::error::Error::ParseError;
use crate::error::{Error, Result};

pub struct HeaderParser<'a> {
    headers: &'a HeaderMap,
}

impl<'a> HeaderParser<'a> {
    /// Create a header parser.
    pub fn new(headers: &'a HeaderMap) -> Self {
        Self { headers }
    }

    /// Parse a header into a string.
    pub fn parse_header<K: AsHeaderName>(&self, header: K) -> Result<Option<String>> {
        self.headers
            .get(header)
            .map(|content_type| {
                Ok::<_, Error>(
                    content_type
                        .to_str()
                        .map_err(|err| ParseError(err.to_string()))?
                        .to_string(),
                )
            })
            .transpose()
    }
}
