import { Construct } from 'constructs';
import { Duration, Stack } from 'aws-cdk-lib';
import { ITableV2 } from 'aws-cdk-lib/aws-dynamodb';
import { EventBus, Rule, IEventBus } from 'aws-cdk-lib/aws-events';
import { Runtime, Architecture } from 'aws-cdk-lib/aws-lambda';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { ISecurityGroup, IVpc, Vpc, VpcLookupOptions, SecurityGroup } from 'aws-cdk-lib/aws-ec2';
import { LambdaFunction } from 'aws-cdk-lib/aws-events-targets';
import { PolicyStatement } from 'aws-cdk-lib/aws-iam';
import * as path from 'path';

export interface Icav2EventTranslatorConstructProps {
  /** dynamodb name and event bus name */
  icav2EventTranslatorDynamodbTable: ITableV2;
  eventBusName: string;
  /** vpc ann SG for lambda function */
  vpcProps: VpcLookupOptions;
  lambdaSecurityGroupName: string;
}

export class IcaEventTranslatorConstruct extends Construct {
  private readonly vpc: IVpc;
  private readonly lambdaSG: ISecurityGroup;
  private readonly mainBus: IEventBus;
  private readonly dynamoDBTable: ITableV2;
  private readonly lambdaRuntimePythonVersion = Runtime.PYTHON_3_12;

  constructor(scope: Construct, id: string, props: Icav2EventTranslatorConstructProps) {
    super(scope, id);
    this.dynamoDBTable = props.icav2EventTranslatorDynamodbTable;
    this.mainBus = EventBus.fromEventBusName(this, 'EventBus', props.eventBusName);
    this.vpc = Vpc.fromLookup(this, 'MainVpc', props.vpcProps);
    this.lambdaSG = SecurityGroup.fromLookupByName(
      this,
      'LambdaSecurityGroup',
      props.lambdaSecurityGroupName,
      this.vpc
    );

    this.createICAv2EventTranslator(props);
  }

  private createICAv2EventTranslator(props: Icav2EventTranslatorConstructProps) {
    const EventTranslatorFunction = new PythonFunction(this, 'EventTranslator', {
      entry: path.join(__dirname, '../translator_service'),
      runtime: this.lambdaRuntimePythonVersion,
      environment: {
        TABLE_NAME: props.icav2EventTranslatorDynamodbTable.tableName,
        EVENT_BUS_NAME: props.eventBusName,
      },
      vpc: this.vpc,
      vpcSubnets: { subnets: this.vpc.privateSubnets },
      securityGroups: [this.lambdaSG],
      architecture: Architecture.ARM_64,
      timeout: Duration.seconds(28),
      index: 'icav2_event_translator.py',
      handler: 'handler',
    });

    this.dynamoDBTable.grantReadWriteData(EventTranslatorFunction);

    // Create a rule to trigger the Lambda function from the EventBus ICAV2_EXTERNAL_EVENT
    const rule = new Rule(this, 'Rule', {
      eventBus: this.mainBus,
      eventPattern: {
        account: [Stack.of(this).account],
        detailType: ['Event from aws:sqs'],
        detail: {
          'ica-event': {
            eventCode: [{ prefix: 'ICA_EXEC_' }],
            projectId: [{ exists: true }],
          },
        },
      },
    });

    rule.addTarget(
      new LambdaFunction(EventTranslatorFunction, {
        maxEventAge: Duration.seconds(60), // Maximum age for an event to be retried, Member must have value greater than or equal to 60 (Service: EventBridge)
        retryAttempts: 3, // Retry up to 3 times
      })
    );

    // Optional: If the Lambda function needs more permissions for the DynamoDB table and the event bus
    EventTranslatorFunction.addToRolePolicy(
      new PolicyStatement({
        actions: ['events:PutEvents', 'dynamodb:PutItem'],
        resources: [this.mainBus.eventBusArn, this.dynamoDBTable.tableArn],
      })
    );
  }
}
