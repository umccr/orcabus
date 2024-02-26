use sqlx::query_file;

use crate::database::Client;
use crate::error::Result;

/// Query the filemanager via REST interface.
#[derive(Debug)]
pub struct Query {
    client: Client,
}

pub struct QueryResults {
    results: Vec<String>, // FIXME: Adjust return type
}

impl Query {
    /// Creates a new filemanager query client.
    pub fn new(client: Client) -> Self {
        Self { client }
    }

    /// Creates a new filemanager query client with default connection settings.
    pub async fn with_defaults() -> Result<Self> {
        Ok(Self {
            client: Client::default().await?,
        })
    }

    pub async fn query_objects(&self, query: String) -> Result<QueryResults> {
        let query_results = query_file!("../database/queries/api/select_object_ids.sql", 
                                            &query)
                                .execute
                                .await?;
        todo!()
    }
}