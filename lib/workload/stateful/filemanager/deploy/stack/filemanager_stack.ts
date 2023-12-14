import { Duration, RemovalPolicy, Stack, StackProps, Tags } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as iam from 'aws-cdk-lib/aws-iam';
import { RustFunction, Settings as CargoSettings } from 'rust.aws-cdk-lambda';
import { Architecture } from 'aws-cdk-lib/aws-lambda';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as lambdaDestinations from 'aws-cdk-lib/aws-lambda-destinations';
import * as lambdaEventSources from 'aws-cdk-lib/aws-lambda-event-sources';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as s3n from 'aws-cdk-lib/aws-s3-notifications';

/**
 * Common settings for the filemanager stack.
 */
interface Settings {
  database_url: string;
  endpoint_url?: string;
  stack_name: string;
  buildEnvironment?: NodeJS.ProcessEnv;
}

/**
 * Stack used to deploy filemanager.
 */
export class FilemanagerStack extends Stack {
  constructor(scope: Construct, id: string, settings: Settings, props?: StackProps) {
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
      removalPolicy: RemovalPolicy.DESTROY,
    });

    testBucket.addEventNotification(s3.EventType.OBJECT_CREATED, new s3n.SqsDestination(queue));
    testBucket.addEventNotification(s3.EventType.OBJECT_REMOVED, new s3n.SqsDestination(queue));

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

    // VPC
    //const vpc = ec2.Vpc.fromLookup(this, 'main-vpc', { isDefault: false });
    const vpc = new ec2.Vpc(this, 'vpc', {
      ipAddresses: ec2.IpAddresses.cidr('10.0.0.0/24'),
      maxAzs: 99, // As many as there are available in the region
      natGateways: 1,
      subnetConfiguration: [
        {
          name: 'ingress',
          subnetType: ec2.SubnetType.PUBLIC,
        },
        {
          name: 'application',
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
        },
        {
          name: 'database',
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
        },
      ],
    });

    // Secret
    new secretsmanager.Secret(this, 'filemanager_db_secret', {
      secretName: 'filemanager_db_secret', // pragma: allowlist secret
      generateSecretString: {
        secretStringTemplate: JSON.stringify({ username: 'filemanager' }),
        excludePunctuation: true,
        generateStringKey: 'password',
      },
    });

    // RDS
    new rds.ServerlessCluster(this, 'Database', {
      engine: rds.DatabaseClusterEngine.auroraPostgres({
        version: rds.AuroraPostgresEngineVersion.VER_13_12,
      }),
      defaultDatabaseName: 'filemanager',
      credentials: rds.Credentials.fromGeneratedSecret('filemanager_db_secret'),
      removalPolicy: RemovalPolicy.DESTROY,
      vpc,
    });
  }
}
