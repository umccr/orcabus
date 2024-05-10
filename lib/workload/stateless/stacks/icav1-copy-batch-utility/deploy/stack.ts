import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import path from 'path';
import { Duration, aws_secretsmanager } from 'aws-cdk-lib';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { Architecture, Runtime } from 'aws-cdk-lib/aws-lambda';

export interface ICAv1CopyBatchUtilityConfig {
  AppName: string;
  Icav1TokenSecretId: string;
  BucketForCopyDestination: string;
  BucketForManifestOrInventory: string;
  BucketForBatchOpsReport: string;
  TransferMaximumConcurrency: number;
  TransferMaxPoolConnections: number;
  TransferMaxErrorRetries: number;
  TransferMultiPartChunkSize: number;
}

export type ICAv1CopyBatchUtilityStackProps = ICAv1CopyBatchUtilityConfig & cdk.StackProps;

export class ICAv1CopyBatchUtilityStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: ICAv1CopyBatchUtilityStackProps) {
    super(scope, id, props);

    // Get ICAv1 Access token secret object for construct
    const icav1_token = aws_secretsmanager.Secret.fromSecretNameV2(
      this,
      'Icav1Secret',
      props.Icav1TokenSecretId
    );

    // S3 Batch Ops lambda
    const lambda = new PythonFunction(this, 'ICAv1 Copy Batch Utility lambda', {
      entry: path.join(__dirname, '../lambdas'),
      runtime: Runtime.PYTHON_3_12,
      environment: {
        destination_bucket: props.BucketForCopyDestination,
        max_concurrency: props.TransferMaximumConcurrency.toString(),
        max_pool_connections: props.TransferMaxPoolConnections.toString(),
        max_attempts: props.TransferMaxErrorRetries.toString(),
        multipart_chunksize: props.TransferMultiPartChunkSize.toString(),
      },
      architecture: Architecture.ARM_64,
      timeout: Duration.seconds(28),
      index: 'lambda.py',
      handler: 'handler',
    });

    // Attach S3 Batch Operations job assumed roles and policies
  }
}
