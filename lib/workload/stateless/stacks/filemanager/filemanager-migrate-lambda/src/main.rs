use aws_lambda_events::cloudformation::provider::CloudFormationCustomResourceRequest;
use aws_sdk_cloudformation::types::StackStatus;
use aws_sdk_cloudformation::Client;
use filemanager::clients::aws::config;
use filemanager::database::aws::migration::Migration;
use filemanager::database::Client as DbClient;
use filemanager::database::Migrate;
use filemanager::env::Config;
use filemanager::handlers::aws::{create_database_pool, update_credentials};
use filemanager::handlers::init_tracing;
use lambda_runtime::{run, service_fn, Error, LambdaEvent};
use tracing::trace;

#[tokio::main]
async fn main() -> Result<(), Error> {
    init_tracing();

    let config = &Config::load()?;
    let options = &create_database_pool(config).await?;
    let cfn_client = &Client::new(&config::Config::with_defaults().await.load());

    run(service_fn(
        |event: LambdaEvent<CloudFormationCustomResourceRequest>| async move {
            update_credentials(options, config).await?;

            // Migrate depending on the type of lifecycle event using the CDK provider framework:
            // https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.custom_resources-readme.html#provider-framework
            match event.payload {
                // Migrate normally if this resource is being created.
                CloudFormationCustomResourceRequest::Create(create) => {
                    trace!(create = ?create, "during create");

                    Ok::<_, Error>(
                        Migration::new(DbClient::new(options.clone()))
                            .migrate()
                            .await?,
                    )
                }
                // If this is an update event, then we need to check if a rollback is in progress.
                CloudFormationCustomResourceRequest::Update(update) => {
                    trace!(update = ?update, "during update");

                    // Find the state of the top-level stack which is being updated. This will
                    // contain a status indicating if this is the first update, or a rollback update.
                    let stack_state = cfn_client
                        .describe_stacks()
                        .stack_name(update.common.stack_id.as_str())
                        .send()
                        .await?
                        .stacks
                        .and_then(|stacks| {
                            stacks.into_iter().find(|stack| {
                                stack.stack_id() == Some(update.common.stack_id.as_str())
                            })
                        })
                        .and_then(|stack| stack.stack_status);

                    // Only migrate when this is a normal update.
                    if let Some(ref status) = stack_state {
                        trace!(stack_state = ?stack_state);

                        if let StackStatus::UpdateInProgress = status {
                            return Ok::<_, Error>(
                                Migration::new(DbClient::new(options.clone()))
                                    .migrate()
                                    .await?,
                            );
                        }
                    }

                    // If this was a rollback update, then no migration should be performed,
                    // because the previous update indicated a failed migration, and the migration
                    // would have already been rolled back. If a migration occurred here it would
                    // just fail again, resulting in an `UPDATE_ROLLBACK_FAILED`.
                    Ok(())
                }
                // If this is a delete event, there is nothing to do.
                CloudFormationCustomResourceRequest::Delete(delete) => {
                    trace!(delete = ?delete, "during delete");

                    Ok(())
                }
            }
        },
    ))
    .await
}
