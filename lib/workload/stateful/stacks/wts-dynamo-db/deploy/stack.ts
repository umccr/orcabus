import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { DynamodbPartitionedPipelineConstruct } from '../../../../components/dynamodb-partitioned-table';

export interface WtsIcav2PipelineTableConfig {
  dynamodbTableName: string;
  wtsIcav2DynamodbTableArnSsmParameterPath: string;
  wtsIcav2DynamodbTableNameSsmParameterPath: string;
}

export type WtsIcav2PipelineTableStackProps = WtsIcav2PipelineTableConfig & cdk.StackProps;

export class WtsIcav2PipelineTable extends cdk.Stack {
  public readonly wtsIcav2DynamodbTableArnSsmParameterPath: string;
  public readonly wtsIcav2DynamodbTableNameSsmParameterPath: string;

  constructor(scope: Construct, id: string, props: WtsIcav2PipelineTableStackProps) {
    super(scope, id, props);

    /*
    Initialise dynamodb table, where portal_run_id is the primary sort key
    */
    const dynamodb_table = new DynamodbPartitionedPipelineConstruct(
      this,
      'wts_icav2_pipeline_table',
      {
        tableName: props.dynamodbTableName,
      }
    );

    /*
    Generate a ssm parameter to store the table arn so it can be referred to be other stacks
    */
    this.wtsIcav2DynamodbTableArnSsmParameterPath = new ssm.StringParameter(
      this,
      'wts_icav2_pipeline_table_arn_ssm_path',
      {
        parameterName: props.wtsIcav2DynamodbTableArnSsmParameterPath,
        stringValue: dynamodb_table.tableNameArn,
      }
    ).parameterName;

    this.wtsIcav2DynamodbTableNameSsmParameterPath = new ssm.StringParameter(
      this,
      'wts_icav2_pipeline_table_name_ssm_path',
      {
        parameterName: props.wtsIcav2DynamodbTableNameSsmParameterPath,
        stringValue: props.dynamodbTableName,
      }
    ).parameterName;
  }
}
