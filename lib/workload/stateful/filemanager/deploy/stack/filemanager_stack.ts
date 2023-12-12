import { Fn, Duration, RemovalPolicy, Stack, StackProps, Tags, Environment } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as iam from 'aws-cdk-lib/aws-iam';
import { RustFunction, Settings as CargoSettings } from 'rust.aws-cdk-lambda';
import { Architecture } from 'aws-cdk-lib/aws-lambda';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as rds from 'aws-cdk-lib/aws-rds';
import { CfnBucket } from 'aws-cdk-lib/aws-s3';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as lambdaDestinations from 'aws-cdk-lib/aws-lambda-destinations';
import * as lambdaEventSources from 'aws-cdk-lib/aws-lambda-event-sources';
import * as ec2 from 'aws-cdk-lib/aws-ec2';

/**
 * Common settings for the filemanager stack.
 */
interface Settings {
  database_url: string;
  endpoint_url?: string;
  force_path_style: boolean; //FIXME: Does this refer to buckets? We cannot do this forever as AWS will move to domain style?
  stack_name: string;
  buildEnvironment?: NodeJS.ProcessEnv;
}

/**
 * Stack used to deploy filemanager.
 */
export class FilemanagerStack extends Stack {
  constructor(
    scope: Construct,
    id: string,
    env: Environment,
    settings: Settings,
    props?: StackProps
  ) {
    super(scope, id, props);

    Tags.of(this).add('Stack', settings.stack_name);

    const lambdaRole = new iam.Role(this, id + 'Role', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      description: 'Lambda execution role for ' + id,
    });

    const queue = new sqs.Queue(this, id + 'Queue');

    const testBucket = new s3.Bucket(this, id + 'Bucket', {
      bucketName: 'filemanager-test-ingest',
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      removalPolicy: RemovalPolicy.RETAIN,
    });

    const cfnBucket = testBucket.node.defaultChild as CfnBucket;
    cfnBucket.notificationConfiguration = {
      queueConfigurations: [
        {
          event: 's3:ObjectCreated:*',
          queue: queue.queueArn,
        },
        {
          event: 's3:ObjectRemoved:*',
          queue: queue.queueArn,
        },
      ],
    };

    // testBucket.addEventNotification(s3.EventType.OBJECT_CREATED, new s3n.SqsDestination(queue));
    // testBucket.addEventNotification(s3.EventType.OBJECT_REMOVED, new s3n.SqsDestination(queue));

    lambdaRole.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaSQSQueueExecutionRole')
    );

    const s3BucketPolicy = new iam.PolicyStatement({
      actions: ['s3:List*', 's3:Get*'],
      resources: ['arn:aws:s3:::*'],
    });
    lambdaRole.addToPolicy(s3BucketPolicy);

    const deadLetterQueue = new sqs.Queue(this, id + 'DeadLetterQueue');
    const deadLetterQueueDestination = new lambdaDestinations.SqsDestination(deadLetterQueue);

    CargoSettings.WORKSPACE_DIR = '../';
    CargoSettings.BUILD_INDIVIDUALLY = true;

    const filemanagerLambda = new RustFunction(this, id + 'IngestLambdaFunction', {
      package: 'filemanager-ingest-lambda',
      target: 'aarch64-unknown-linux-gnu',

      memorySize: 128,
      timeout: Duration.seconds(28),
      environment: {
        DATABASE_URL: settings.database_url,
        ...(settings.endpoint_url && { ENDPOINT_URL: settings.endpoint_url }),
        FORCE_PATH_STYLE: settings.force_path_style.toString(),
        SQS_QUEUE_URL: queue.queueUrl,
        RUST_LOG: 'info,filemanager_ingest_lambda=trace,filemanager=trace',
      },
      buildEnvironment: settings.buildEnvironment,
      architecture: Architecture.ARM_64,
      role: lambdaRole,
      onFailure: deadLetterQueueDestination,
    });

    const eventSource = new lambdaEventSources.SqsEventSource(queue);
    filemanagerLambda.addEventSource(eventSource);

    // RDS
    const vpc = ec2.Vpc.fromLookup(this, 'main-vpc', { isDefault: true });
    new rds.DatabaseCluster(this, 'Database', {
      engine: rds.DatabaseClusterEngine.auroraPostgres({
        version: rds.AuroraPostgresEngineVersion.VER_15_3,
      }),
      serverlessV2MinCapacity: 0.5,
      serverlessV2MaxCapacity: 3,
      writer: rds.ClusterInstance.provisioned('writer'),
      readers: [rds.ClusterInstance.serverlessV2('reader')],
      vpc,
    });
  }
}
