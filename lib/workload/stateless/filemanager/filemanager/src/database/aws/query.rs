use sqlx::{ Row, query_file };

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
    pub async fn query_objects(&self, query: String) -> Result<QueryResults> {

        let mut tx = self.client.pool().begin().await?;

        let query_results: Vec<String> = query_file!("../database/queries/api/select_object_ids.sql", &query)
            .fetch_all(&mut *tx)
            .await?
            .into_iter()
            .map(|row| row.get(0))
            .collect();

        tx.commit().await?;

        let query_results = QueryResults::new(query_results); // Convert PgQueryResult to QueryResults
        Ok(query_results)
    }
}

impl QueryResults {
    pub fn new(results: Vec<String>) -> Self {
        Self { results }
    } 
}