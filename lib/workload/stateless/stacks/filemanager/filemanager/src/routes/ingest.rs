//! Route logic for ingesting entries into the database.
//!

#[double]
use crate::clients::aws::s3::Client as S3Client;
#[double]
use crate::clients::aws::sqs::Client as SQSClient;
use crate::error::Result;
use crate::handlers::aws::receive_and_ingest;
use crate::routes::{AppState, ErrorStatusCode};
use axum::extract::State;
use axum::Json;
use mockall_double::double;
use serde::Deserialize;

/// Params for ingesting from the SQS queue.
#[derive(Debug, Deserialize)]
pub struct IngestFromSQS {}

/// The ingest from sqs handler.
#[utoipa::path(
    post,
    path = "/ingest_from_sqs",
    responses(
        (status = NO_CONTENT, description = "Ingest objects into the database from the SQS queue", body = ()),
        ErrorStatusCode,
    ),
    context_path = "/file/v1",
)]
pub async fn ingest_from_sqs(state: State<AppState>) -> Result<Json<()>> {
    receive_and_ingest(
        S3Client::with_defaults().await,
        SQSClient::with_defaults().await,
        None::<String>,
        &state.client,
        &state.config,
    )
    .await?;

    Ok(Json(()))
}
