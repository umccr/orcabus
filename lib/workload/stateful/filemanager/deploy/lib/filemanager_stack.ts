import { Duration, RemovalPolicy, Stack, StackProps, Tags } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as iam from 'aws-cdk-lib/aws-iam';
import { RustFunction, Settings as CargoSettings } from 'rust.aws-cdk-lambda';
import { Architecture } from 'aws-cdk-lib/aws-lambda';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as lambdaDestinations from 'aws-cdk-lib/aws-lambda-destinations';
import * as lambdaEventSources from 'aws-cdk-lib/aws-lambda-event-sources';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as s3n from 'aws-cdk-lib/aws-s3-notifications';
import { IngestFunction, IngestFunctionSettings } from '../constructs/functions/ingest';
import { Database, EnableMonitoringProps, DatabaseSettings } from '../constructs/database';

/**
 * Common settings for the filemanager stack.
 */
type Settings = DatabaseSettings &
  IngestFunctionSettings & {
    databaseName?: string;
  };

/**
 * Stack used to deploy filemanager.
 */
export class FilemanagerStack extends Stack {
  constructor(scope: Construct, id: string, props: StackProps, settings?: Settings) {
    super(scope, id, props);

    const queue = new sqs.Queue(this, id + 'Queue');

    const testBucket = new s3.Bucket(this, id + 'Bucket', {
      bucketName: 'filemanager-test-ingest',
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      removalPolicy: RemovalPolicy.DESTROY,
    });
    const testBucketPolicy = new iam.PolicyStatement({
      actions: ['s3:List*', 's3:Get*'],
      resources: ['arn:aws:s3:::*'],
    });
    testBucket.addEventNotification(s3.EventType.OBJECT_CREATED, new s3n.SqsDestination(queue));
    testBucket.addEventNotification(s3.EventType.OBJECT_REMOVED, new s3n.SqsDestination(queue));

    const deadLetterQueue = new sqs.Queue(this, id + 'DeadLetterQueue');
    const deadLetterQueueDestination = new lambdaDestinations.SqsDestination(deadLetterQueue);

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

    const secret = new secretsmanager.Secret(this, 'FilemanagerDatabaseSecret', {
      secretName: 'FilemanagerDatabaseSecret', // pragma: allowlist secret
      generateSecretString: {
        secretStringTemplate: JSON.stringify({ username: 'filemanager' }),
        excludePunctuation: true,
        generateStringKey: 'password',
      },
    });

    const database = new Database(this, 'Database', {
      vpc,
      databaseName: settings?.databaseName ?? 'filemanager',
      secret,
      destroyOnRemove: settings?.destroyOnRemove,
      enableMonitoring: settings?.enableMonitoring,
      minCapacity: settings?.minCapacity,
      maxCapacity: settings?.maxCapacity,
      port: settings?.port,
    });

    new IngestFunction(this, 'IngestLambda', {
      vpc,
      database,
      queue,
      onFailure: deadLetterQueueDestination,
      policies: [testBucketPolicy],
      buildEnvironment: settings?.buildEnvironment,
      rustLog: settings?.rustLog,
    });
  }
}
