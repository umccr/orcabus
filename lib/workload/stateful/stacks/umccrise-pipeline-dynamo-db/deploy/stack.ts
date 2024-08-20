import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { DynamodbPartitionedPipelineConstruct } from '../../../../components/dynamodb-partitioned-table';

export interface UmccriseIcav2PipelineTableConfig {
  dynamodbTableName: string;
  umccriseIcav2DynamodbTableArnSsmParameterPath: string;
  umccriseIcav2DynamodbTableNameSsmParameterPath: string;
}

export type UmccriseIcav2PipelineTableStackProps = UmccriseIcav2PipelineTableConfig &
  cdk.StackProps;

export class UmccriseIcav2PipelineTable extends cdk.Stack {
  public readonly umccriseIcav2DynamodbTableArnSsmParameterPath: string;
  public readonly umccriseIcav2DynamodbTableNameSsmParameterPath: string;

  constructor(scope: Construct, id: string, props: UmccriseIcav2PipelineTableStackProps) {
    super(scope, id, props);

    /*
    Initialise dynamodb table, where portal_run_id is the primary sort key
    */
    const dynamodb_table = new DynamodbPartitionedPipelineConstruct(
      this,
      'umccrise_icav2_pipeline_table',
      {
        tableName: props.dynamodbTableName,
      }
    );

    /*
    Generate a ssm parameter to store the table arn so it can be referred to be other stacks
    */
    this.umccriseIcav2DynamodbTableArnSsmParameterPath = new ssm.StringParameter(
      this,
      'umccrise_icav2_pipeline_table_arn_ssm_path',
      {
        parameterName: props.umccriseIcav2DynamodbTableArnSsmParameterPath,
        stringValue: dynamodb_table.tableNameArn,
      }
    ).parameterName;

    this.umccriseIcav2DynamodbTableNameSsmParameterPath = new ssm.StringParameter(
      this,
      'umccrise_icav2_pipeline_table_name_ssm_path',
      {
        parameterName: props.umccriseIcav2DynamodbTableNameSsmParameterPath,
        stringValue: props.dynamodbTableName,
      }
    ).parameterName;
  }
}
