import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
// import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { DYNAMODB_SSM_PARAMETER_PATH } from '../constants';

export class BclconvertInteropQcDynamoDBTable extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // The code that defines your stack goes here

    // example resource
    // const queue = new sqs.Queue(this, 'DeployQueue', {
    //   visibilityTimeout: cdk.Duration.seconds(300)
    // });

    /*
    Initialise dynamodb table, where portal_run_id is the primary sort key
    */
    const dynamodb_table = new dynamodb.Table(this, 'BclconvertInteropQcDynamoDBTable', {
      partitionKey: {
        name: 'portal_run_id',
        type: dynamodb.AttributeType.STRING,
      },
      tableName: 'bclconvertInteropQcICAv2AnalysesDynamoDBTable',
    });

    /*
    Generate a ssm parameter to store the table arn so it can be referred to be other stacks
    */
    const dynamodb_table_ssm_parameter = new ssm.StringParameter(
      this,
      'BclconvertInteropQcDynamoDBTableArn',
      {
        parameterName: DYNAMODB_SSM_PARAMETER_PATH,
        stringValue: dynamodb_table.tableArn,
      }
    );
  }
}
