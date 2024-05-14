use sqlx::{query_file, Acquire, Postgres, QueryBuilder, Row};

use crate::database::Client;
use crate::error::Result;
use crate::events::aws::FlatS3EventMessage;

/// Query the filemanager via REST interface.
#[derive(Debug)]
pub struct Query<'a> {
    client: Client<'a>,
}

pub struct QueryResults {
    _results: Vec<String>, // FIXME: Adjust return type
}

impl<'a> Query<'a> {
    /// Creates a new filemanager query client.
    pub fn new(client: Client<'a>) -> Self {
        Self { client }
    }

    /// Creates a new filemanager query client with default connection settings.
    /// -- FIXME: Should not trust user input, should be a bit more robust than like/similar to
    pub async fn query_objects(&self, query: String) -> Result<QueryResults> {
        let mut tx = self.client.pool().begin().await?;

        let query_results: Vec<String> =
            query_file!("../database/queries/api/select_object_ids.sql", &query)
                .fetch_all(&mut *tx)
                .await?
                .into_iter()
                .map(|row| row.get(0))
                .collect();

        tx.commit().await?;

        let query_results = QueryResults::new(query_results); // Convert PgQueryResult to QueryResults
        Ok(query_results)
    }

    /// Selects existing objects by the bucket and key. This does not start a transaction.
    /// TODO, ideally this should use some better types. Potentially use sea-orm codegen to simplify.
    pub async fn select_existing_by_bucket_key(
        &self,
        conn: impl Acquire<'_, Database = Postgres>,
        bucket: &str,
        key: &str,
        version_id: Option<String>,
        for_update: bool,
    ) -> Result<FlatS3EventMessage> {
        let mut conn = conn.acquire().await?;

        let version_id = version_id.unwrap_or_else(FlatS3EventMessage::default_version_id);

        let mut builder: QueryBuilder<Postgres> = QueryBuilder::new(include_str!(
            "../../../../database/queries/api/select_existing_by_bucket_key.sql"
        ));

        builder.push_bind(bucket);
        builder.push_bind(key);
        builder.push_bind(version_id);

        if for_update {
            builder.push("for_update;");
        } else {
            builder.push(";");
        }

        Ok(builder
            .build_query_as::<FlatS3EventMessage>()
            .fetch_one(&mut *conn)
            .await?)
    }
}

impl QueryResults {
    pub fn new(_results: Vec<String>) -> Self {
        Self { _results }
    }
}
