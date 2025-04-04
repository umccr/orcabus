//! Functions related to parsing header information.
//!

use crate::error::Error::{MissingHostHeader, ParseError};
use crate::error::{Error, Result};
use aws_lambda_events::http::header::HOST;
use axum::extract::{OriginalUri, Request};
use axum::http::header::AsHeaderName;
use axum::http::HeaderMap;
use url::Url;

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

    /// Parse a request into a URL based on the HOST.
    pub fn parse_host_url(request: &Request, use_tls_links: bool) -> Result<Url> {
        let mut host = HeaderParser::new(request.headers())
            .parse_header(HOST)?
            .ok_or_else(|| MissingHostHeader)?;

        // A `HOST` is not a valid URL yet.
        if !host.starts_with("https://") && !host.starts_with("http://") {
            if use_tls_links {
                host = format!("https://{}", host);
            } else {
                host = format!("http://{}", host);
            }
        }

        Ok(host.parse()?)
    }

    /// Get the path from the request, including possible nesting.
    pub fn get_uri_path(request: &Request) -> String {
        if let Some(path) = request.extensions().get::<OriginalUri>() {
            path.0.to_string()
        } else {
            request.uri().to_string()
        }
    }
}
