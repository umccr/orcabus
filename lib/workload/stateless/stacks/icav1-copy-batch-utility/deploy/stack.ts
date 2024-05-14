import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import path from 'path';
import { Duration, aws_secretsmanager } from 'aws-cdk-lib';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { Architecture, Runtime } from 'aws-cdk-lib/aws-lambda';
import { aws_iam as iam } from 'aws-cdk-lib';

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
    // const icav1_token = aws_secretsmanager.Secret.fromSecretNameV2(
    //   this,
    //   'Icav1Secret',
    //   props.Icav1TokenSecretId
    // );

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
    const s3BatchCopyLambdaFunctionIamRole = new iam.Role(
      this,
      'S3BatchCopyLambdaFunctionIamRole',
      {
        assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
        managedPolicies: [
          iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
        ],
      }
    );

    s3BatchCopyLambdaFunctionIamRole.addToPolicy(
      new iam.PolicyStatement({
        actions: [
          's3:GetObject',
          's3:GetObjectAcl',
          's3:GetObjectTagging',
          's3:GetObjectVersion',
          's3:GetObjectVersionAcl',
          's3:GetObjectVersionTagging',
          's3:ListBucket*',
        ],
        resources: ['*'],
        effect: iam.Effect.ALLOW,
      })
    );

    s3BatchCopyLambdaFunctionIamRole.addToPolicy(
      new iam.PolicyStatement({
        actions: [
          's3:PutObject',
          's3:PutObjectAcl',
          's3:PutObjectTagging',
          's3:PutObjectLegalHold',
          's3:PutObjectRetention',
          's3:GetBucketObjectLockConfiguration',
          's3:ListBucket*',
          's3:GetBucketLocation',
        ],
        resources: [
          `arn:aws:s3:::${props.BucketForCopyDestination}`,
          `arn:aws:s3:::${props.BucketForCopyDestination}/*`,
        ],
        effect: iam.Effect.ALLOW,
      })
    );

    // Attach S3 Batch Operations service IAM role
    const s3BatchOperationsServiceIamRole = new iam.Role(this, 'S3BatchOperationsServiceIamRole', {
      assumedBy: new iam.ServicePrincipal('batchoperations.s3.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });
    s3BatchOperationsServiceIamRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ['sts:AssumeRole'],
        resources: [s3BatchCopyLambdaFunctionIamRole.roleArn],
        effect: iam.Effect.ALLOW,
      })
    );
  }
}
