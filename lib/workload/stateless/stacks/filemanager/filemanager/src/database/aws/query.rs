use sqlx::{query_file, query_file_as, Acquire, Postgres, Row, Transaction};

use crate::database::Client;
use crate::error::Result;
use crate::events::aws::message::EventType;
use crate::events::aws::{FlatS3EventMessage, FlatS3EventMessages, StorageClass};

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

    /// Selects existing objects by the bucket and key for update. This does not start a transaction.
    /// TODO, ideally this should use some better types. Potentially use sea-orm codegen to simplify queries.
    pub async fn select_existing_by_bucket_key(
        &self,
        conn: impl Acquire<'_, Database = Postgres>,
        buckets: &[String],
        keys: &[String],
        version_ids: &[String],
    ) -> Result<FlatS3EventMessages> {
        let mut conn = conn.acquire().await?;

        Ok(FlatS3EventMessages(
            query_file_as!(
                FlatS3EventMessage,
                "../database/queries/api/select_existing_by_bucket_key.sql",
                buckets,
                keys,
                version_ids
            )
            .fetch_all(&mut *conn)
            .await?,
        ))
    }

    /// Start a new transaction.
    pub async fn transaction(&self) -> Result<Transaction<Postgres>> {
        Ok(self.client.pool().begin().await?)
    }
}

impl QueryResults {
    pub fn new(_results: Vec<String>) -> Self {
        Self { _results }
    }
}

#[cfg(test)]
mod tests {
    use std::ops::Add;

    use chrono::{DateTime, Duration};
    use sqlx::PgPool;

    use crate::database::aws::ingester::tests::{test_events, test_ingester};
    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::database::Ingest;
    use crate::events::aws::message::EventType::Created;
    use crate::events::aws::tests::{EXPECTED_NEW_SEQUENCER_ONE, EXPECTED_VERSION_ID};
    use crate::events::EventSourceType::S3;

    use super::*;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_select_existing_by_bucket_key(pool: PgPool) {
        let ingester = test_ingester(pool.clone());
        let query = Query::new(Client::from_pool(pool));

        let events = test_events(Some(Created));

        let new_date = Some(DateTime::default().add(Duration::days(1)));
        let new_sequencer = Some(EXPECTED_NEW_SEQUENCER_ONE.to_string());
        let new_key = "key1";

        let mut increase_date = test_events(Some(Created));
        increase_date.event_times[0] = new_date;
        increase_date.sequencers[0].clone_from(&new_sequencer);

        let mut different_key = test_events(Some(Created));
        different_key.keys[0] = new_key.to_string();

        let mut different_key_and_date = test_events(Some(Created));
        different_key_and_date.event_times[0] = new_date;
        different_key_and_date.keys[0] = new_key.to_string();
        different_key_and_date.sequencers[0].clone_from(&new_sequencer);

        ingester.ingest(S3(events)).await.unwrap();
        ingester.ingest(S3(increase_date)).await.unwrap();
        ingester.ingest(S3(different_key)).await.unwrap();
        ingester.ingest(S3(different_key_and_date)).await.unwrap();

        let mut tx = query.client.pool().begin().await.unwrap();
        let results = query
            .select_existing_by_bucket_key(
                &mut tx,
                vec!["bucket".to_string(), "bucket".to_string()].as_slice(),
                vec!["key".to_string(), new_key.to_string()].as_slice(),
                vec![
                    EXPECTED_VERSION_ID.to_string(),
                    EXPECTED_VERSION_ID.to_string(),
                ]
                .as_slice(),
            )
            .await
            .unwrap()
            .0;

        assert_eq!(results.len(), 2);
        assert!(results
            .first()
            .iter()
            .all(|result| result.bucket == "bucket"
                && result.key == "key"
                && result.event_time == new_date));
        assert!(results.get(1).iter().all(|result| result.bucket == "bucket"
            && result.key == new_key
            && result.event_time == new_date));
    }
}
