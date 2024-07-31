import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { DynamodbPartitionedPipelineConstruct } from '../../../../components/dynamodb-partitioned-table';

export interface TnIcav2PipelineTableConfig {
  dynamodbTableName: string;
  tnIcav2DynamodbTableArnSsmParameterPath: string;
  tnIcav2DynamodbTableNameSsmParameterPath: string;
}

export type TnIcav2PipelineTableStackProps = TnIcav2PipelineTableConfig & cdk.StackProps;

export class TnIcav2PipelineTable extends cdk.Stack {
  public readonly tnIcav2DynamodbTableArnSsmParameterPath: string;
  public readonly tnIcav2DynamodbTableNameSsmParameterPath: string;

  constructor(scope: Construct, id: string, props: TnIcav2PipelineTableStackProps) {
    super(scope, id, props);

    /*
    Initialise dynamodb table, where portal_run_id is the primary sort key
    */
    const dynamodb_table = new DynamodbPartitionedPipelineConstruct(
      this,
      'tn_icav2_pipeline_table',
      {
        tableName: props.dynamodbTableName,
      }
    );

    /*
    Generate a ssm parameter to store the table arn so it can be referred to be other stacks
    */
    this.tnIcav2DynamodbTableArnSsmParameterPath = new ssm.StringParameter(
      this,
      'tn_icav2_pipeline_table_arn_ssm_path',
      {
        parameterName: props.tnIcav2DynamodbTableArnSsmParameterPath,
        stringValue: dynamodb_table.tableNameArn,
      }
    ).parameterName;

    this.tnIcav2DynamodbTableNameSsmParameterPath = new ssm.StringParameter(
      this,
      'tn_icav2_pipeline_table_name_ssm_path',
      {
        parameterName: props.tnIcav2DynamodbTableNameSsmParameterPath,
        stringValue: props.dynamodbTableName,
      }
    ).parameterName;
  }
}
