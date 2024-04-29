import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { DynamodbIcav2PipelineConstruct } from '../../../../components/dynamodb-icav2-table';

export interface Cttsov2Icav2PipelineTableConfig {
  dynamodb_table_name: string;
  cttsov2_icav2_dynamodb_table_arn_ssm_parameter_path: string;
  cttsov2_icav2_dynamodb_table_name_ssm_parameter_path: string;
}

export type Cttsov2Icav2PipelineTableStackProps = Cttsov2Icav2PipelineTableConfig & cdk.StackProps;

export class Cttsov2Icav2PipelineTable extends cdk.Stack {
  public readonly cttsov2_icav2_dynamodb_table_arn_ssm_parameter_path: string;
  public readonly cttsov2_icav2_dynamodb_table_name_ssm_parameter_path: string;

  constructor(scope: Construct, id: string, props: Cttsov2Icav2PipelineTableStackProps) {
    super(scope, id, props);

    /*
    Initialise dynamodb table, where portal_run_id is the primary sort key
    */
    const dynamodb_table = new DynamodbIcav2PipelineConstruct(
      this,
      'cttsov2_icav2_pipeline_table',
      {
        table_name: props.dynamodb_table_name,
      }
    );

    /*
    Generate a ssm parameter to store the table arn so it can be referred to be other stacks
    */
    this.cttsov2_icav2_dynamodb_table_arn_ssm_parameter_path = new ssm.StringParameter(
      this,
      'cttsov2_icav2_pipeline_table_arn_ssm_path',
      {
        parameterName: props.cttsov2_icav2_dynamodb_table_arn_ssm_parameter_path,
        stringValue: dynamodb_table.table_name_arn,
      }
    ).parameterName;

    this.cttsov2_icav2_dynamodb_table_name_ssm_parameter_path = new ssm.StringParameter(
      this,
      'cttsov2_icav2_pipeline_table_name_ssm_path',
      {
        parameterName: props.cttsov2_icav2_dynamodb_table_name_ssm_parameter_path,
        stringValue: props.dynamodb_table_name,
      }
    ).parameterName;
  }
}
