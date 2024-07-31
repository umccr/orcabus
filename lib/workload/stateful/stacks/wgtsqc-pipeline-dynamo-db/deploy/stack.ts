import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { DynamodbPartitionedPipelineConstruct } from '../../../../components/dynamodb-partitioned-table';

export interface WgtsQcIcav2PipelineTableConfig {
  dynamodbTableName: string;
  wgtsQcIcav2DynamodbTableArnSsmParameterPath: string;
  wgtsQcIcav2DynamodbTableNameSsmParameterPath: string;
}

export type WgtsQcIcav2PipelineTableStackProps = WgtsQcIcav2PipelineTableConfig & cdk.StackProps;

export class WgtsQcIcav2PipelineTable extends cdk.Stack {
  public readonly wgtsQcIcav2DynamodbTableArnSsmParameterPath: string;
  public readonly wgtsQcIcav2DynamodbTableNameSsmParameterPath: string;

  constructor(scope: Construct, id: string, props: WgtsQcIcav2PipelineTableStackProps) {
    super(scope, id, props);

    /*
    Initialise dynamodb table, where portal_run_id is the primary sort key
    */
    const dynamodb_table = new DynamodbPartitionedPipelineConstruct(
      this,
      'wgtsqc_icav2_pipeline_table',
      {
        tableName: props.dynamodbTableName,
      }
    );

    /*
    Generate a ssm parameter to store the table arn so it can be referred to be other stacks
    */
    this.wgtsQcIcav2DynamodbTableArnSsmParameterPath = new ssm.StringParameter(
      this,
      'wgtsqc_icav2_pipeline_table_arn_ssm_path',
      {
        parameterName: props.wgtsQcIcav2DynamodbTableArnSsmParameterPath,
        stringValue: dynamodb_table.tableNameArn,
      }
    ).parameterName;

    this.wgtsQcIcav2DynamodbTableNameSsmParameterPath = new ssm.StringParameter(
      this,
      'wgtsqc_icav2_pipeline_table_name_ssm_path',
      {
        parameterName: props.wgtsQcIcav2DynamodbTableNameSsmParameterPath,
        stringValue: props.dynamodbTableName,
      }
    ).parameterName;
  }
}
