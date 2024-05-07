import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { PythonLambdaLayerConstruct } from '../../../../components/python-lambda-layer';
import path from 'path';
import { aws_secretsmanager } from 'aws-cdk-lib';

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
  //  public readonly icav2_copy_batch_state_machine_arn_ssm_parameter_path: string;

  constructor(scope: Construct, id: string, props: ICAv1CopyBatchUtilityStackProps) {
    super(scope, id, props);

    // Get ICAv1 Access token secret object for construct
    // const icav1_access_token_secret_obj = aws_secretsmanager.Secret.fromSecretNameV2(
    //   this,
    //   'Icav1SecretsObject',
    //   props.Icav1TokenSecretId
    // );

    // Generate lambda layer
    const lambda_layer = new PythonLambdaLayerConstruct(this, 'lambda_layer', {
      layerDescription: 'ICAv1 Copy Batch Utility Tools',
      layerDirectory: path.join(__dirname, '../layers'),
      layerName: 'icav1_copy_batch_utility_tools',
    });

    // Attach S3 Batch Operations job assumed roles and policies
  }
}
