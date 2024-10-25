import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { DynamodbPartitionedPipelineConstruct } from '../../../../components/dynamodb-partitioned-table';

export interface OncoanalyserNfPipelineTableConfig {
  dynamodbTableName: string;
  oncoanalyserNfDynamodbTableArnSsmParameterPath: string;
  oncoanalyserNfDynamodbTableNameSsmParameterPath: string;
}

export type OncoanalyserNfPipelineTableStackProps = OncoanalyserNfPipelineTableConfig &
  cdk.StackProps;

export class OncoanalyserNfPipelineTable extends cdk.Stack {
  public readonly oncoanalyserNfDynamodbTableArnSsmParameterPath: string;
  public readonly oncoanalyserNfDynamodbTableNameSsmParameterPath: string;

  constructor(scope: Construct, id: string, props: OncoanalyserNfPipelineTableStackProps) {
    super(scope, id, props);

    /*
    Initialise dynamodb table, where portal_run_id is the primary sort key
    */
    const dynamodb_table = new DynamodbPartitionedPipelineConstruct(
      this,
      'oncoanalyser_nf_pipeline_table',
      {
        tableName: props.dynamodbTableName,
      }
    );

    /*
    Generate a ssm parameter to store the table arn so it can be referred to be other stacks
    */
    this.oncoanalyserNfDynamodbTableArnSsmParameterPath = new ssm.StringParameter(
      this,
      'oncoanalyser_nf_pipeline_table_arn_ssm_path',
      {
        parameterName: props.oncoanalyserNfDynamodbTableArnSsmParameterPath,
        stringValue: dynamodb_table.tableNameArn,
      }
    ).parameterName;

    this.oncoanalyserNfDynamodbTableNameSsmParameterPath = new ssm.StringParameter(
      this,
      'oncoanalyser_nf_pipeline_table_name_ssm_path',
      {
        parameterName: props.oncoanalyserNfDynamodbTableNameSsmParameterPath,
        stringValue: props.dynamodbTableName,
      }
    ).parameterName;
  }
}
