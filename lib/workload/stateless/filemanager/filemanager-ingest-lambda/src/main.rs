use aws_lambda_events::event::sqs::SqsEventObj;
use lambda_runtime::{run, service_fn, Error, LambdaEvent};
use serde::{Deserialize, Serialize};

/// Object that you send to SQS and plan to process on the function.
#[derive(Deserialize, Serialize)]
struct Data {
    todo: String,
}

/// This is the main body for the function.
/// You can use the data sent into SQS here.
async fn function_handler(event: LambdaEvent<SqsEventObj<Data>>) -> Result<(), Error> {
    todo!();
}

#[tokio::main]
async fn main() -> Result<(), Error> {
    // required to enable CloudWatch error logging by the runtime
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        // disable printing the name of the module in every log line.
        .with_target(false)
        // disabling time is handy because CloudWatch will add the ingestion time.
        .without_time()
        .init();

    run(service_fn(function_handler)).await
}