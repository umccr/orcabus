import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import path from 'path';
import { Duration, aws_ssm } from 'aws-cdk-lib';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { Architecture, LayerVersion, Runtime } from 'aws-cdk-lib/aws-lambda';
import { aws_iam as iam } from 'aws-cdk-lib';

export interface ICAv1CopyBatchUtilityConfig {
  AppName: string;
  Icav1TokenSecretId: string;
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

    // ICA
    /// ICA v1 SSM parameters
    new aws_ssm.StringParameter(this, 'IcaV1AccessKeyId', {
      parameterName: 'IcaV1AccessKeyId',
      stringValue: 'null', // To be filled by rotator lambda
    });

    new aws_ssm.StringParameter(this, 'IcaV1SecretAccessKey', {
      parameterName: 'IcaV1SecretAccessKey',
      stringValue: 'null', // To be filled by rotator lambda
    });

    new aws_ssm.StringParameter(this, 'IcaV1SessionToken', {
      parameterName: 'IcaV1SessionToken',
      stringValue: 'null', // To be filled by rotator lambda
    });

    /// ICA v1 creds rotator
    const ica_v1_creds_lambda = new PythonFunction(this, 'ICAv1 credentials lambda', {
      entry: path.join(__dirname, '../lambdas'),
      runtime: Runtime.PYTHON_3_12,
      role: lambdaRole,
      architecture: Architecture.ARM_64,
      timeout: Duration.seconds(28),
      index: 'ica_aws_secrets_rotator.py',
      handler: 'handler',
    });

    // Allow lambda access to secretsmanager secret 'IcaSecretsPortal'
    ica_v1_creds_lambda.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['secretsmanager:GetSecretValue', 'ssm:PutParameter'],
        resources: [
          `arn:aws:secretsmanager:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:secret:IcaSecretsPortal*`,
          `arn:aws:ssm:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:parameter/icav1_aws_access_key_id`,
          `arn:aws:ssm:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:parameter/icav1_aws_secret_access_key`,
          `arn:aws:ssm:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:parameter/icav1_aws_session_token`,
        ],
      })
    );

    // ICA v1 creds rotator cron job
    const cronJob = new cdk.aws_events.Rule(this, 'ICAv1 Creds Rotator CronJob', {
      schedule: cdk.aws_events.Schedule.cron({ minute: '0', hour: '0' }), // Run every day at midnight
      targets: [new cdk.aws_events_targets.LambdaFunction(ica_v1_creds_lambda)],
    });

    // S3 Batch Ops lambda
    const s3_batch_ops_lambda = new PythonFunction(
      this,
      'ICAv1 Copy Batch Utility lambda - Boto3',
      {
        entry: path.join(__dirname, '../lambdas'),
        runtime: Runtime.PYTHON_3_12,
        role: lambdaRole,
        environment: {
          destination_bucket: props.BucketForCopyDestination,
          destination_bucket_prefix: props.BucketForCopyDestinationPrefix,
          max_concurrency: props.TransferMaximumConcurrency.toString(),
          max_pool_connections: props.TransferMaxPoolConnections.toString(),
          max_attempts: props.TransferMaxErrorRetries.toString(),
          multipart_chunksize: props.TransferMultiPartChunkSize.toString(),
        },
        architecture: Architecture.ARM_64,
        timeout: Duration.seconds(28),
        index: 's3_batch_ops_boto3.py',
        handler: 'handler',
      }
    );

    // FIXME: Add the layer building code here instead of relying on a pre-build/uploaded rclone layer
    const rclone_layer_ref = LayerVersion.fromLayerVersionArn(
      this,
      'RClone Layer',
      'arn:aws:lambda:ap-southeast-2:843407916570:layer:rclone-arm64:1'
    );

    const s3_batch_ops_rclone_lambda = new PythonFunction(
      this,
      'ICAv1 Copy Batch Utility lambda - RClone',
      {
        entry: path.join(__dirname, '../layers/src/rclone'),
        runtime: Runtime.PYTHON_3_12,
        layers: [rclone_layer_ref],
        role: lambdaRole,
        // environment: {
        //   // Creds
        //   SECURE_SRC_AWS_ACCESS_KEY_ID: "None",       // pragma: allowlist secret
        //   SECURE_SRC_AWS_SECRET_ACCESS_KEY: "None",   // pragma: allowlist secret
        //   SECURE_SRC_AWS_SESSION_TOKEN: "None",       // pragma: allowlist secret
        //   SECURE_DEST_AWS_ACCESS_KEY_ID: "None",      // pragma: allowlist secret
        //   SECURE_DEST_AWS_SECRET_ACCESS_KEY: "None",  // pragma: allowlist secret
        //   SECURE_DEST_AWS_SESSION_TOKEN: "None",      // pragma: allowlist secret
        //   // Objects
        //   RCLONE_SYNC_CONTENT_SOURCE: "None",
        //   RCLONE_SYNC_CONTENT_DESTINATION: "None",
        // },
        architecture: Architecture.ARM_64,
        timeout: Duration.minutes(15),
        index: 's3_batch_ops_rclone.py',
        handler: 'handler',
      }
    );

    s3_batch_ops_rclone_lambda.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['ssm:GetParameter'],
        resources: [
          `arn:aws:ssm:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:parameter/rclone-config`,
          `arn:aws:ssm:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:parameter/icav1_aws_access_key_id`,
          `arn:aws:ssm:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:parameter/icav1_aws_secret_access_key`,
          `arn:aws:ssm:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:parameter/icav1_aws_session_token`,
        ],
      })
    );

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
                `arn:aws:lambda:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:function:${s3_batch_ops_lambda.functionName}*`,
                `arn:aws:lambda:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:function:${s3_batch_ops_rclone_lambda.functionName}*`,
                //`arn:aws:lambda:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:function:${ica_v1_creds_lambda.functionName}*`,
              ],
              effect: iam.Effect.ALLOW,
            }),
          ],
        }),
      },
    });
  }
}
