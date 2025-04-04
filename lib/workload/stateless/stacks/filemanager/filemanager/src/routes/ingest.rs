//! Route logic for ingesting entries into the database.
//!

use axum::extract::State;
use axum::routing::post;
use axum::{Json, Router};
use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

use crate::error::Result;
use crate::handlers::aws::receive_and_ingest;
use crate::routes::error::ErrorStatusCode;
use crate::routes::AppState;

/// The return value for ingest endpoints indicating how many records were processed.
#[derive(Debug, Deserialize, Serialize, ToSchema)]
#[serde(rename_all = "camelCase")]
pub struct IngestCount {
    /// The number of events processed. This potentially includes duplicate records.
    n_records: usize,
}

/// Ingest events from the configured SQS queue.
#[utoipa::path(
    post,
    path = "/ingest",
    responses(
        (status = OK, description = "A successful ingestion with the number of ingested records", body = IngestCount),
        ErrorStatusCode,
    ),
    context_path = "/api/v1",
    tag = "ingest",
)]
pub async fn ingest_from_sqs(state: State<AppState>) -> Result<Json<IngestCount>> {
    let n_records = receive_and_ingest(
        state.s3_client().clone(),
        state.sqs_client().clone(),
        None::<String>,
        &state.database_client,
        &state.config,
    )
    .await?;

    Ok(Json(IngestCount { n_records }))
}

/// The router for ingesting events.
pub fn ingest_router() -> Router<AppState> {
    Router::new().route("/ingest", post(ingest_from_sqs))
}

#[cfg(test)]
mod tests {
    use std::sync::Arc;

    use axum::body::Body;
    use axum::http::{Method, Request};
    use sqlx::PgPool;
    use tower::util::ServiceExt;

    use crate::database::aws::migration::tests::MIGRATOR;
    use crate::handlers::aws::tests::test_receive_and_ingest_with;
    use crate::routes::{api_router, AppState};

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_from_sqs_api(pool: PgPool) {
        let mut state = AppState::from_pool(pool).await.unwrap();
        Arc::get_mut(&mut state.config)
            .unwrap()
            .sqs_url
            .get_or_insert("url".to_string());

        let database = state.database_client().clone();
        test_receive_and_ingest_with(&database, |sqs_client, s3_client| async {
            state.sqs_client = Arc::new(sqs_client);
            state.s3_client = Arc::new(s3_client);

            let app = api_router(state.clone()).unwrap();
            app.oneshot(
                Request::builder()
                    .method(Method::POST)
                    .uri("/ingest")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        })
        .await;
    }
}
