import { Construct } from 'constructs';
import { Duration, Stack, RemovalPolicy } from 'aws-cdk-lib';
import { TableV2, AttributeType } from 'aws-cdk-lib/aws-dynamodb';
import { EventBus, Rule, IEventBus } from 'aws-cdk-lib/aws-events';
import { Runtime, Architecture } from 'aws-cdk-lib/aws-lambda';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { ISecurityGroup, IVpc, Vpc, VpcLookupOptions, SecurityGroup } from 'aws-cdk-lib/aws-ec2';
import { LambdaFunction } from 'aws-cdk-lib/aws-events-targets';
import { PolicyStatement } from 'aws-cdk-lib/aws-iam';
import * as path from 'path';

export interface Icav2EventTranslatorConstructProps {
  /** dynamodb name and event bus name */
  icav2EventTranslatorDynamodbTableName: string;
  dynamodbTableRemovalPolicy: RemovalPolicy;
  eventBusName: string;
  /** vpc ann SG for lambda function */
  vpcProps: VpcLookupOptions;
  lambdaSecurityGroupName: string;
  /** ica event pipe name for tight coupling */
  icaEventPipeName: string;
}

export class IcaEventTranslatorConstruct extends Construct {
  private readonly vpc: IVpc;
  private readonly lambdaSG: ISecurityGroup;
  private readonly mainBus: IEventBus;
  private readonly lambdaRuntimePythonVersion = Runtime.PYTHON_3_12;

  constructor(scope: Construct, id: string, props: Icav2EventTranslatorConstructProps) {
    super(scope, id);
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
    // create the dynamodb table for the translator service
    const dynamoDBTable = new TableV2(this, 'ICAv2EventTranslatorDynamoDBTable', {
      tableName: props.icav2EventTranslatorDynamodbTableName,
      removalPolicy: props.dynamodbTableRemovalPolicy,

      /* Either a db_uuid or an icav2 event id or a portal run id */
      partitionKey: { name: 'analysis_id', type: AttributeType.STRING },
      sortKey: { name: 'event_status', type: AttributeType.STRING },
    });

    const EventTranslatorFunction = new PythonFunction(this, 'EventTranslator', {
      entry: path.join(__dirname, '../translator_service'),
      runtime: this.lambdaRuntimePythonVersion,
      environment: {
        TABLE_NAME: props.icav2EventTranslatorDynamodbTableName,
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

    dynamoDBTable.grantReadWriteData(EventTranslatorFunction);

    // Create a rule to trigger the Lambda function from the EventBus ICAV2_EXTERNAL_EVENT
    const rule = new Rule(this, 'Rule', {
      eventBus: this.mainBus,
      eventPattern: {
        account: [Stack.of(this).account],
        detailType: ['Event from aws:sqs'],
        source: [`Pipe ${props.icaEventPipeName}`],
        detail: {
          'ica-event': {
            eventCode: [{ prefix: 'ICA_EXEC_' }],
            projectId: [{ exists: true }],
            payload: [{ exists: true }],
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
        actions: ['events:PutEvents', 'dynamodb:PutItem', 'dynamodb:GetItem', 'dynamodb:Scan'],
        resources: [this.mainBus.eventBusArn, dynamoDBTable.tableArn],
      })
    );
  }
}
