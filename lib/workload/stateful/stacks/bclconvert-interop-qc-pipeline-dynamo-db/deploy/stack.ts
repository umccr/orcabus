import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { DynamodbIcav2PipelineConstruct } from '../../../../components/dynamodb-icav2-table';

export interface BclconvertInteropQcIcav2PipelineTableConfig {
  dynamodbTableName: string;
  bclconvertInteropQcIcav2DynamodbTableArnSsmParameterPath: string;
  bclconvertInteropQcIcav2DynamodbTableNameSsmParameterPath: string;
}

export type BclconvertInteropQcIcav2PipelineTableStackProps =
  BclconvertInteropQcIcav2PipelineTableConfig & cdk.StackProps;

export class BclconvertInteropQcIcav2PipelineTableStack extends cdk.Stack {
  public readonly bclconvertInteropQcIcav2DynamodbTableArnSsmParameterPath: string;
  public readonly bclconvertInteropQcIcav2DynamodbTableNameSsmParameterPath: string;

  constructor(
    scope: Construct,
    id: string,
    props: BclconvertInteropQcIcav2PipelineTableStackProps
  ) {
    super(scope, id, props);

    /*
    Initialise dynamodb table, where portal_run_id is the primary sort key
    */
    const dynamodb_table = new DynamodbIcav2PipelineConstruct(
      this,
      'bclconvertInteropQc_icav2_pipeline_table',
      {
        tableName: props.dynamodbTableName,
      }
    );

    /*
    Generate a ssm parameter to store the table arn so it can be referred to be other stacks
    */
    this.bclconvertInteropQcIcav2DynamodbTableArnSsmParameterPath = new ssm.StringParameter(
      this,
      'bclconvertInteropQc_icav2_pipeline_table_arn_ssm_path',
      {
        parameterName: props.bclconvertInteropQcIcav2DynamodbTableArnSsmParameterPath,
        stringValue: dynamodb_table.tableNameArn,
      }
    ).parameterName;

    this.bclconvertInteropQcIcav2DynamodbTableNameSsmParameterPath = new ssm.StringParameter(
      this,
      'bclconvertInteropQc_icav2_pipeline_table_name_ssm_path',
      {
        parameterName: props.bclconvertInteropQcIcav2DynamodbTableNameSsmParameterPath,
        stringValue: props.dynamodbTableName,
      }
    ).parameterName;
  }
}
