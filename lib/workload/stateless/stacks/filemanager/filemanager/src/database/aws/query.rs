use sqlx::{query, query_as, Acquire, PgConnection, Postgres, Transaction};

use crate::database::Client;
use crate::error::Result;
use crate::events::aws::{FlatS3EventMessage, FlatS3EventMessages};

/// Query the filemanager via REST interface.
#[derive(Debug)]
pub struct Query {
    client: Client,
}

impl Query {
    /// Creates a new filemanager query client.
    pub fn new(client: Client) -> Self {
        Self { client }
    }

    /// Selects existing objects by the bucket and key for update. This does not start a transaction.
    /// TODO, ideally this should use some better types. Potentially use sea-orm codegen to simplify queries.
    pub async fn select_existing_by_bucket_key(
        &self,
        conn: &mut PgConnection,
        buckets: &[String],
        keys: &[String],
        version_ids: &[String],
    ) -> Result<FlatS3EventMessages> {
        Ok(FlatS3EventMessages(
            query_as::<_, FlatS3EventMessage>(include_str!(
                "../../../../database/queries/api/select_existing_by_bucket_key.sql"
            ))
            .bind(buckets)
            .bind(keys)
            .bind(version_ids)
            .fetch_all(conn)
            .await?,
        ))
    }

    pub async fn reset_current_state(
        &self,
        conn: &mut PgConnection,
        buckets: &[String],
        keys: &[String],
        version_ids: &[String],
        sequencers: &[Option<String>],
    ) -> Result<()> {
        let conn = conn.acquire().await?;

        query(include_str!(
            "../../../../database/queries/api/reset_current_state.sql"
        ))
        .bind(buckets)
        .bind(keys)
        .bind(version_ids)
        .bind(sequencers)
        .execute(&mut *conn)
        .await?;

        Ok(())
    }

    /// Start a new transaction.
    pub async fn transaction(&self) -> Result<Transaction<Postgres>> {
        Ok(self.client.pool().begin().await?)
    }
}

#[cfg(test)]
mod tests {
    use std::ops::Add;

    use crate::database::aws::ingester::tests::test_events;
    use crate::database::aws::ingester::Ingester;
    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::events::aws::message::EventType::Created;
    use crate::events::aws::tests::{
        EXPECTED_NEW_SEQUENCER_ONE, EXPECTED_SEQUENCER_CREATED_ONE, EXPECTED_VERSION_ID,
    };
    use chrono::{DateTime, Duration, Utc};
    use sqlx::PgPool;

    use super::*;

    async fn ingest_test_records(pool: PgPool) -> (String, Option<DateTime<Utc>>) {
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

        Ingester::ingest_query(&events, &mut pool.acquire().await.unwrap())
            .await
            .unwrap();
        Ingester::ingest_query(&increase_date, &mut pool.acquire().await.unwrap())
            .await
            .unwrap();
        Ingester::ingest_query(&different_key, &mut pool.acquire().await.unwrap())
            .await
            .unwrap();
        Ingester::ingest_query(&different_key_and_date, &mut pool.acquire().await.unwrap())
            .await
            .unwrap();

        (new_key.to_string(), new_date)
    }

    async fn query_current_state(
        new_key: &String,
        query: &Query,
        conn: &mut PgConnection,
    ) -> Vec<FlatS3EventMessage> {
        query
            .select_existing_by_bucket_key(
                conn,
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
            .0
    }

    async fn query_reset_current_state(
        new_key: &String,
        query: &Query,
        sequencer: &str,
        conn: &mut PgConnection,
    ) {
        query
            .reset_current_state(
                conn,
                vec!["bucket".to_string(), "bucket".to_string()].as_slice(),
                vec!["key".to_string(), new_key.to_string()].as_slice(),
                vec![
                    EXPECTED_VERSION_ID.to_string(),
                    EXPECTED_VERSION_ID.to_string(),
                ]
                .as_slice(),
                vec![Some(sequencer.to_string()), Some(sequencer.to_string())].as_slice(),
            )
            .await
            .unwrap();
    }

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_select_existing_by_bucket_key(pool: PgPool) {
        let (new_key, new_date) = ingest_test_records(pool.clone()).await;
        let client = Client::from_pool(pool);
        let query = Query::new(client);

        let mut tx = query.client.pool().begin().await.unwrap();
        let results = query_current_state(&new_key, &query, &mut tx).await;
        tx.commit().await.unwrap();

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

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn test_reset_current_state(pool: PgPool) {
        let (new_key, _) = ingest_test_records(pool.clone()).await;
        let client = Client::from_pool(pool);
        let query = Query::new(client);

        let mut tx = query.client.pool().begin().await.unwrap();
        query_reset_current_state(&new_key, &query, EXPECTED_NEW_SEQUENCER_ONE, &mut tx).await;

        let results = query_current_state(&new_key, &query, &mut tx).await;

        tx.commit().await.unwrap();

        for result in results {
            if result.sequencer == Some(EXPECTED_SEQUENCER_CREATED_ONE.to_string()) {
                assert!(!result.is_current_state);
            } else {
                assert!(result.is_current_state);
            }
        }
    }
}
