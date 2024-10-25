import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { DynamodbPartitionedPipelineConstruct } from '../../../../components/dynamodb-partitioned-table';

export interface SashNfPipelineTableConfig {
  dynamodbTableName: string;
  sashNfDynamodbTableArnSsmParameterPath: string;
  sashNfDynamodbTableNameSsmParameterPath: string;
}

export type SashNfPipelineTableStackProps = SashNfPipelineTableConfig & cdk.StackProps;

export class SashNfPipelineTable extends cdk.Stack {
  public readonly sashNfDynamodbTableArnSsmParameterPath: string;
  public readonly sashNfDynamodbTableNameSsmParameterPath: string;

  constructor(scope: Construct, id: string, props: SashNfPipelineTableStackProps) {
    super(scope, id, props);

    /*
    Initialise dynamodb table, where portal_run_id is the primary sort key
    */
    const dynamodb_table = new DynamodbPartitionedPipelineConstruct(
      this,
      'sash_nf_pipeline_table',
      {
        tableName: props.dynamodbTableName,
      }
    );

    /*
    Generate a ssm parameter to store the table arn so it can be referred to be other stacks
    */
    this.sashNfDynamodbTableArnSsmParameterPath = new ssm.StringParameter(
      this,
      'sash_nf_pipeline_table_arn_ssm_path',
      {
        parameterName: props.sashNfDynamodbTableArnSsmParameterPath,
        stringValue: dynamodb_table.tableNameArn,
      }
    ).parameterName;

    this.sashNfDynamodbTableNameSsmParameterPath = new ssm.StringParameter(
      this,
      'sash_nf_pipeline_table_name_ssm_path',
      {
        parameterName: props.sashNfDynamodbTableNameSsmParameterPath,
        stringValue: props.dynamodbTableName,
      }
    ).parameterName;
  }
}
