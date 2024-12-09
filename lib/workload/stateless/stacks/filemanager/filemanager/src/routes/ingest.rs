//! Route logic for ingesting entries into the database.
//!

use axum::extract::State;
use axum::routing::post;
use axum::{Json, Router};
use mockall_double::double;
use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

#[double]
use crate::clients::aws::s3::Client as S3Client;
#[double]
use crate::clients::aws::sqs::Client as SQSClient;
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
        S3Client::with_defaults().await,
        SQSClient::with_defaults().await,
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

    use super::*;

    #[sqlx::test(migrator = "MIGRATOR")]
    async fn ingest_from_sqs_api(pool: PgPool) {
        let mut state = AppState::from_pool(pool).await;
        Arc::get_mut(&mut state.config)
            .unwrap()
            .sqs_url
            .get_or_insert("url".to_string());

        test_receive_and_ingest_with(state.database_client(), |sqs_client, s3_client| async {
            let sqs_ctx = SQSClient::with_defaults_context();
            sqs_ctx.expect().return_once(|| sqs_client);
            let s3_ctx = S3Client::with_defaults_context();
            s3_ctx.expect().return_once(|| s3_client);

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
