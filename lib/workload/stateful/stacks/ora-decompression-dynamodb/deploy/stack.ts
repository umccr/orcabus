import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { DynamodbPartitionedPipelineConstruct } from '../../../../components/dynamodb-partitioned-table';

export interface OraCompressionIcav2PipelineTableConfig {
  dynamodbTableName: string;
  oraDecompressionIcav2DynamodbTableArnSsmParameterPath: string;
  oraDecompressionIcav2DynamodbTableNameSsmParameterPath: string;
}

export type OraCompressionIcav2PipelineTableStackProps = OraCompressionIcav2PipelineTableConfig &
  cdk.StackProps;

export class OraCompressionIcav2PipelineTable extends cdk.Stack {
  public readonly oraCompressionIcav2DynamodbTableArnSsmParameterPath: string;
  public readonly oraCompressionIcav2DynamodbTableNameSsmParameterPath: string;

  constructor(scope: Construct, id: string, props: OraCompressionIcav2PipelineTableStackProps) {
    super(scope, id, props);

    /*
    Initialise dynamodb table, where portal_run_id is the primary sort key
    */
    const dynamodb_table = new DynamodbPartitionedPipelineConstruct(
      this,
      'ora_decompression_icav2_pipeline_table',
      {
        tableName: props.dynamodbTableName,
      }
    );

    /*
    Generate a ssm parameter to store the table arn so it can be referred to be other stacks
    */
    this.oraCompressionIcav2DynamodbTableArnSsmParameterPath = new ssm.StringParameter(
      this,
      'ora_decompression_icav2_pipeline_table_arn_ssm_path',
      {
        parameterName: props.oraDecompressionIcav2DynamodbTableArnSsmParameterPath,
        stringValue: dynamodb_table.tableNameArn,
      }
    ).parameterName;

    this.oraCompressionIcav2DynamodbTableNameSsmParameterPath = new ssm.StringParameter(
      this,
      'ora_decompression_icav2_pipeline_table_name_ssm_path',
      {
        parameterName: props.oraDecompressionIcav2DynamodbTableNameSsmParameterPath,
        stringValue: props.dynamodbTableName,
      }
    ).parameterName;
  }
}
