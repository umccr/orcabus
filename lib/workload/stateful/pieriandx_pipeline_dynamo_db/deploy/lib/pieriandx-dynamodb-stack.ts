import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
// import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { DYNAMODB_TABLE_ARN_SSM_PARAMETER_PATH, DYNAMODB_TABLE_NAME, DYNAMODB_TABLE_NAME_SSM_PARAMETER_PATH } from '../constants';
import * as ssm from 'aws-cdk-lib/aws-ssm';


export class PieriandxDynamodbStack extends cdk.Stack {

  public readonly pieriandx_dynamodb_arn_ssm_parameter_path: string;
  public readonly pieriandx_dynamodb_table_name_ssm_parameter_path: string;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    /*
    Initialise dynamodb table, where portal_run_id is the primary sort key
    */
    const dynamodb_table = new dynamodb.TableV2(this, 'PierianDxDynamoDBTable', {
      /* Either a db_uuid or an icav2 analysis id or a portal run id */
      partitionKey: {
        name: 'id',
        type: dynamodb.AttributeType.STRING,
      },
      /* One of 'db_uuid', 'portal_run_id', 'case_id', 'case_accession_number', 'informaticsjob_id' */
      sortKey: {
        name: 'id_type',
        type: dynamodb.AttributeType.STRING,
      },
      tableName: DYNAMODB_TABLE_NAME,
    });

    /*
    Generate a ssm parameter to store the table arn so it can be referred to be other stacks
    */
    this.pieriandx_dynamodb_arn_ssm_parameter_path = new ssm.StringParameter(
      this,
      'PierianDxDynamoDBTableArn',
      {
        parameterName: DYNAMODB_TABLE_ARN_SSM_PARAMETER_PATH,
        stringValue: dynamodb_table.tableArn,
      }
    ).parameterName;

    this.pieriandx_dynamodb_table_name_ssm_parameter_path = new ssm.StringParameter(
      this,
      'PierianDxDynamoDBTableName',
      {
        parameterName: DYNAMODB_TABLE_NAME_SSM_PARAMETER_PATH,
        stringValue: dynamodb_table.tableName,
      }
    ).parameterName;
  }
}
