import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import {
  DYNAMODB_TABLE_ARN_SSM_PARAMETER_PATH,
  DYNAMODB_TABLE_NAME,
  DYNAMODB_TABLE_NAME_SSM_PARAMETER_PATH,
} from './constants';

export class ICAv2EventTranslatorDynamoDBTable extends cdk.Stack {
  public readonly icav2_event_translator_dynamodb_arn_ssm_parameter_path: string;
  public readonly icav2_event_translator_dynamodb_table_name_ssm_parameter_path: string;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // The code that defines your stack goes heres

    /*
    Initialise dynamodb table, where portal_run_id is the primary sort key
    */
    const dynamodb_table = new dynamodb.Table(this, 'ICAv2EventTranslatorDynamoDBTable', {
      /* Either a db_uuid or an icav2 event id or a portal run id */
      partitionKey: {
        name: 'id',
        type: dynamodb.AttributeType.STRING,
      },
      /* translate event created time stamp */
      sortKey: {
        name: 'icav2_analysis_id',
        type: dynamodb.AttributeType.STRING,
      },
      tableName: DYNAMODB_TABLE_NAME,
    });

    /*
    Generate a ssm parameter to store the table arn so it can be referred to be other stacks
    */
    this.icav2_event_translator_dynamodb_arn_ssm_parameter_path = new ssm.StringParameter(
      this,
      'ICAv2EventTranslatorDynamoDBTableArn',
      {
        parameterName: DYNAMODB_TABLE_ARN_SSM_PARAMETER_PATH,
        stringValue: dynamodb_table.tableArn,
      }
    ).parameterName;

    this.icav2_event_translator_dynamodb_table_name_ssm_parameter_path = new ssm.StringParameter(
      this,
      'ICAv2EventTranslatorDynamoDBTableName',
      {
        parameterName: DYNAMODB_TABLE_NAME_SSM_PARAMETER_PATH,
        stringValue: dynamodb_table.tableName,
      }
    ).parameterName;
  }
}
