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
  Icav1AwsAccessKeyId: string;
  Icav1AwsSecretAccessKey: string;
  Icav1AwsSessionToken: string;
  BucketForCopyDestination: string;
  BucketForCopyDestinationPrefix: string;
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

    // ICAv1 Access token secret
    // const icav1_token = aws_secretsmanager.Secret.fromSecretNameV2(
    //   this,
    //   'Icav1Secret',
    //   props.Icav1TokenSecretId
    // );

    // Lambda execution role
    const lambdaRole = new iam.Role(this, 'lambdaRole', {
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
      inlinePolicies: {
        S3BatchCopyLambdaFunctionIamRolePolicy0: new iam.PolicyDocument({
          statements: [
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
            }),
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
            }),
          ],
        }),
      },
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
    });

    // S3 Batch Ops lambda
    const lambda = new PythonFunction(this, 'ICAv1 Copy Batch Utility lambda', {
      entry: path.join(__dirname, '../lambdas'),
      runtime: Runtime.PYTHON_3_12,
      role: lambdaRole,
      environment: {
        ica_v1_aws_access_key_id: props.Icav1AwsAccessKeyId,
        ica_v1_aws_secret_access_key: props.Icav1AwsSecretAccessKey, //pragma: allowlist secret
        ica_v1_aws_session_token: props.Icav1AwsSessionToken,
        destination_bucket: props.BucketForCopyDestination,
        destination_bucket_prefix: props.BucketForCopyDestinationPrefix,
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

    // S3 Batch Operations role
    new iam.Role(this, 'S3BatchOperationsRole', {
      assumedBy: new iam.ServicePrincipal('batchoperations.s3.amazonaws.com'),
      inlinePolicies: {
        S3BatchOperationPolicy: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              actions: ['s3:GetObject', 's3:GetObjectVersion', 's3:GetBucketLocation'],
              resources: [
                `arn:aws:s3:::${props.BucketForManifestOrInventory}`,
                `arn:aws:s3:::${props.BucketForManifestOrInventory}/*`,
              ],
              effect: iam.Effect.ALLOW,
            }),
            new iam.PolicyStatement({
              actions: ['s3:PutObject', 's3:GetBucketLocation'],
              resources: [
                `arn:aws:s3:::${props.BucketForBatchOpsReport}`,
                `arn:aws:s3:::${props.BucketForBatchOpsReport}/*`,
              ],
              effect: iam.Effect.ALLOW,
            }),
            new iam.PolicyStatement({
              actions: ['lambda:InvokeFunction'],
              resources: [
                `arn:aws:lambda:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:function:${lambda.functionName}*`,
              ],
              effect: iam.Effect.ALLOW,
            }),
          ],
        }),
      },
    });
  }
}
