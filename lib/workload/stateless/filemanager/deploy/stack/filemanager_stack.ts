import {Duration, RemovalPolicy, Stack, StackProps, Tags} from "aws-cdk-lib";
import {Construct} from "constructs";
import * as iam from "aws-cdk-lib/aws-iam";
import {RustFunction, Settings as CargoSettings} from "rust.aws-cdk-lambda";
import {Architecture} from "aws-cdk-lib/aws-lambda";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as s3n from "aws-cdk-lib/aws-s3-notifications";
import * as lambdaDestinations from "aws-cdk-lib/aws-lambda-destinations";
import * as lambdaEventSources from "aws-cdk-lib/aws-lambda-event-sources";
import {CfnBucket} from "aws-cdk-lib/aws-s3";

interface Settings {
    database_url: string,
    endpoint_url: string,
    stack_name: string,
}

/**
 * Stack used to deploy filemanager.
 */
export class FilemanagerStack extends Stack {
    constructor(scope: Construct, id: string, settings: Settings, props?: StackProps) {
        super(scope, id, props);

        Tags.of(this).add("Stack", settings.stack_name);

        const lambdaRole = new iam.Role(this, id + "Role", {
            assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com"),
            description: "Lambda execution role for " + id,
        });

        const queue = new sqs.Queue(this, id + 'Queue');

        const testBucket = new s3.Bucket(this, id + "Bucket", {
            bucketName: 'filemanager-test-ingest',
            blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
            encryption: s3.BucketEncryption.S3_MANAGED,
            enforceSSL: true,
            removalPolicy: RemovalPolicy.RETAIN,
        });

        // Workaround for localstack, see https://github.com/localstack/localstack/issues/3468.
        const cfnBucket = testBucket.node.defaultChild as CfnBucket;
        cfnBucket.notificationConfiguration = {
            queueConfigurations: [
                {
                    event: "s3:ObjectCreated:*",
                    queue: queue.queueArn
                },
                {
                    event: "s3:ObjectRemoved:*",
                    queue: queue.queueArn
                }
            ]
        };

        // testBucket.addEventNotification(s3.EventType.OBJECT_CREATED, new s3n.SqsDestination(queue));
        // testBucket.addEventNotification(s3.EventType.OBJECT_REMOVED, new s3n.SqsDestination(queue));

        lambdaRole.addManagedPolicy(
            iam.ManagedPolicy.fromAwsManagedPolicyName(
                "service-role/AWSLambdaSQSQueueExecutionRole",
            ),
        );

        const s3BucketPolicy = new iam.PolicyStatement({
            actions: ["s3:List*", "s3:Get*"],
            resources: ["arn:aws:s3:::*"],
        });
        lambdaRole.addToPolicy(s3BucketPolicy);

        const deadLetterQueue = new sqs.Queue(this, id + 'DeadLetterQueue');
        const deadLetterQueueDestination = new lambdaDestinations.SqsDestination(deadLetterQueue);

        CargoSettings.WORKSPACE_DIR = "../";
        CargoSettings.BUILD_INDIVIDUALLY = true;

        let filemanagerLambda = new RustFunction(this, id + "IngestLambdaFunction", {
            package: "filemanager-ingest-lambda",
            target: "aarch64-unknown-linux-gnu",

            memorySize: 128,
            timeout: Duration.seconds(28),
            environment: {
                DATABASE_URL: settings.database_url,
                ENDPOINT_URL: settings.endpoint_url,
                SQS_QUEUE_URL: queue.queueUrl,
                RUST_LOG: "info,filemanager=trace,filemanager_http_lambda=trace",
            },
            buildEnvironment: {
                RUSTFLAGS: "-C target-cpu=neoverse-n1",
                CARGO_PROFILE_RELEASE_LTO: "true",
                CARGO_PROFILE_RELEASE_CODEGEN_UNITS: "1",
            },
            architecture: Architecture.ARM_64,
            role: lambdaRole,
            onFailure: deadLetterQueueDestination,
        });

        const eventSource = new lambdaEventSources.SqsEventSource(queue);
        filemanagerLambda.addEventSource(eventSource);

        // todo RDS instance.
    }
}