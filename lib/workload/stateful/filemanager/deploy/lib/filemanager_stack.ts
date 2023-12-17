import { RemovalPolicy, Stack, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as lambdaDestinations from 'aws-cdk-lib/aws-lambda-destinations';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { IngestFunction, IngestFunctionSettings } from '../constructs/functions/ingest';
import { Database, DatabaseSettings } from '../constructs/database';
import { SubnetType } from 'aws-cdk-lib/aws-ec2';
import { SqsDestination } from 'aws-cdk-lib/aws-s3-notifications';
import { Bucket, EventType } from 'aws-cdk-lib/aws-s3';
import { PolicyStatement } from 'aws-cdk-lib/aws-iam';
import { Queue } from 'aws-cdk-lib/aws-sqs';
import { Secret } from 'aws-cdk-lib/aws-secretsmanager';

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

    const queue = new Queue(this, id + 'Queue');

    const testBucket = new Bucket(this, id + 'Bucket', {
      bucketName: 'filemanager-test-ingest',
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      removalPolicy: RemovalPolicy.DESTROY,
    });
    const testBucketPolicy = new PolicyStatement({
      actions: ['s3:List*', 's3:Get*'],
      resources: ['arn:aws:s3:::*'],
    });
    testBucket.addEventNotification(EventType.OBJECT_CREATED, new SqsDestination(queue));
    testBucket.addEventNotification(EventType.OBJECT_REMOVED, new SqsDestination(queue));

    const deadLetterQueue = new Queue(this, id + 'DeadLetterQueue');
    const deadLetterQueueDestination = new lambdaDestinations.SqsDestination(deadLetterQueue);

    const vpc = new ec2.Vpc(this, 'Vpc', {
      maxAzs: 99, // As many as there are available in the region
      natGateways: 1,
      subnetConfiguration: [
        {
          name: 'ingress',
          subnetType: SubnetType.PUBLIC,
        },
        {
          name: 'application',
          subnetType: SubnetType.PRIVATE_WITH_EGRESS,
        },
        {
          name: 'database',
          subnetType: SubnetType.PRIVATE_ISOLATED,
        },
      ],
    });

    const secret = new Secret(this, 'FilemanagerDatabaseSecret', {
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
