use lambda_runtime::{run, service_fn, Error, LambdaEvent};
use serde::de::IgnoredAny;
use serde::Deserialize;
use tracing_subscriber::layer::SubscriberExt;
use tracing_subscriber::util::SubscriberInitExt;
use tracing_subscriber::{fmt, EnvFilter};

use crate::CloudFormationRequest::Delete;
use crate::Event::Provider;
use filemanager::database::aws::migration::Migration;
use filemanager::database::Client as DbClient;
use filemanager::database::Migrate;
use filemanager::handlers::aws::{create_database_pool, update_credentials};

/// The lambda event for this function. This is normally a CloudFormationCustomResourceRequest.
/// If anything else is present, the migrate lambda will still attempt to perform a migration.
#[derive(Debug, Deserialize)]
#[serde(untagged)]
pub enum Event {
    Provider(CloudFormationRequest),
    Ignored(IgnoredAny),
}

/// Deserialize only the Delete type because this is the only event with different behaviour.
/// Todo, replace with `provider::CloudFormationCustomResourceRequest` when it gets released:
/// https://github.com/awslabs/aws-lambda-rust-runtime/pull/846
#[derive(Debug, Deserialize)]
#[serde(tag = "RequestType")]
pub enum CloudFormationRequest {
    Delete,
}

#[tokio::main]
async fn main() -> Result<(), Error> {
    let env_filter = EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info"));

    tracing_subscriber::registry()
        .with(fmt::layer().json().without_time())
        .with(env_filter)
        .init();

    let options = &create_database_pool().await?;
    run(service_fn(|event: LambdaEvent<Event>| async move {
        update_credentials(options).await?;

        // Migrate depending on the type of lifecycle event using the CDK provider framework:
        // https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.custom_resources-readme.html
        //
        // Note, we don't care what's contained within the event, as the action will always be
        // to try and migrate unless this is a Delete event.
        match event.payload {
            // If it's a Delete there's no need to do anything.
            Provider(Delete) => Ok(()),
            _ => {
                // If there's nothing to migrate, then this will just return Ok.
                Ok::<_, Error>(
                    Migration::new(DbClient::from_ref(options))
                        .migrate()
                        .await?,
                )
            }
        }
    }))
    .await
}

#[cfg(test)]
mod test {
    use super::*;
    use crate::CloudFormationRequest::Delete;
    use crate::Event::Ignored;
    use serde_json::{from_value, json};

    #[test]
    fn event_deserialize_provider_delete() {
        // From https://github.com/awslabs/aws-lambda-rust-runtime/blob/a68de584154958c524692cb43dc208d520d05a13/lambda-events/src/fixtures/example-cloudformation-custom-resource-provider-delete-request.json
        let event = json!({
            "RequestType": "Delete",
            "RequestId": "ef70561d-d4ba-42a4-801b-33ad88dafc37",
            "StackId": "arn:aws:cloudformation:us-east-1:123456789012:stack/stack-name/16580499-7622-4a9c-b32f-4eba35da93da",
            "ResourceType": "Custom::MyCustomResourceType",
            "LogicalResourceId": "CustomResource",
            "PhysicalResourceId": "custom-resource-f4bd5382-3de3-4caf-b7ad-1be06b899647",
            "ResourceProperties": {
                "Key1" : "string",
                "Key2" : ["list"],
                "Key3" : { "Key4": "map" }
            }
        });

        // A Provider lifecycle event should deserialize into the Provider enum.
        assert!(matches!(from_value(event).unwrap(), Provider(Delete)));
    }

    #[test]
    fn event_deserialize_ignored_create() {
        // From https://github.com/awslabs/aws-lambda-rust-runtime/blob/a68de584154958c524692cb43dc208d520d05a13/lambda-events/src/fixtures/example-cloudformation-custom-resource-provider-create-request.json
        let event = json!({
            "RequestType": "Create",
            "RequestId": "82304eb2-bdda-469f-a33b-a3f1406d0a52",
            "StackId": "arn:aws:cloudformation:us-east-1:123456789012:stack/stack-name/16580499-7622-4a9c-b32f-4eba35da93da",
            "ResourceType": "Custom::MyCustomResourceType",
            "LogicalResourceId": "CustomResource",
            "ResourceProperties": {
                "Key1": "string",
                "Key2": ["list"],
                "Key3": { "Key4": "map" }
            }
        });

        // Any non-deleted cloud formation event data should be ignored.
        assert!(matches!(from_value(event).unwrap(), Ignored(IgnoredAny)));
    }

    #[test]
    fn event_deserialize_ignored_empty() {
        // Any other data should deserialize into the Ignored enum.
        assert!(matches!(
            from_value(json!({})).unwrap(),
            Ignored(IgnoredAny)
        ));
    }
}
