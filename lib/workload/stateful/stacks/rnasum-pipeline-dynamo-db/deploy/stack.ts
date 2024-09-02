import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { DynamodbPartitionedPipelineConstruct } from '../../../../components/dynamodb-partitioned-table';

export interface RnasumIcav2PipelineTableConfig {
  dynamodbTableName: string;
  rnasumIcav2DynamodbTableArnSsmParameterPath: string;
  rnasumIcav2DynamodbTableNameSsmParameterPath: string;
}

export type RnasumIcav2PipelineTableStackProps = RnasumIcav2PipelineTableConfig & cdk.StackProps;

export class RnasumIcav2PipelineTable extends cdk.Stack {
  public readonly rnasumIcav2DynamodbTableArnSsmParameterPath: string;
  public readonly rnasumIcav2DynamodbTableNameSsmParameterPath: string;

  constructor(scope: Construct, id: string, props: RnasumIcav2PipelineTableStackProps) {
    super(scope, id, props);

    /*
    Initialise dynamodb table, where portal_run_id is the primary sort key
    */
    const dynamodb_table = new DynamodbPartitionedPipelineConstruct(
      this,
      'rnasum_icav2_pipeline_table',
      {
        tableName: props.dynamodbTableName,
      }
    );

    /*
    Generate a ssm parameter to store the table arn so it can be referred to be other stacks
    */
    this.rnasumIcav2DynamodbTableArnSsmParameterPath = new ssm.StringParameter(
      this,
      'rnasum_icav2_pipeline_table_arn_ssm_path',
      {
        parameterName: props.rnasumIcav2DynamodbTableArnSsmParameterPath,
        stringValue: dynamodb_table.tableNameArn,
      }
    ).parameterName;

    this.rnasumIcav2DynamodbTableNameSsmParameterPath = new ssm.StringParameter(
      this,
      'rnasum_icav2_pipeline_table_name_ssm_path',
      {
        parameterName: props.rnasumIcav2DynamodbTableNameSsmParameterPath,
        stringValue: props.dynamodbTableName,
      }
    ).parameterName;
  }
}
