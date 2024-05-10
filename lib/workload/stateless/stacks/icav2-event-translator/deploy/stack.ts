import { Construct } from 'constructs';
import { Duration, Stack, StackProps } from 'aws-cdk-lib';
import { TableV2, ITableV2 } from 'aws-cdk-lib/aws-dynamodb';
import { EventBus, Rule, IEventBus } from 'aws-cdk-lib/aws-events';
import { Runtime, Architecture } from 'aws-cdk-lib/aws-lambda';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { ISecurityGroup, IVpc, Vpc, VpcLookupOptions, SecurityGroup } from 'aws-cdk-lib/aws-ec2';
import { LambdaFunction } from 'aws-cdk-lib/aws-events-targets';
import { PolicyStatement } from 'aws-cdk-lib/aws-iam';
import * as path from 'path';

export interface Icav2EventTranslatorStackProps {
  /** dynamodb name and event bus name */
  icav2EventTranslatorDynamodbTableName: string;
  eventBusName: string;
  /** vpc ann SG for lambda function */
  vpcProps: VpcLookupOptions;
  lambdaSecurityGroupName: string;
}

export class Icav2EventTranslatorStack extends Stack {
  private readonly vpc: IVpc;
  private readonly lambdaSG: ISecurityGroup;
  private readonly mainBus: IEventBus;
  private readonly dynamoDBTable: ITableV2;
  private readonly lambdaRuntimePythonVersion = Runtime.PYTHON_3_12;

  constructor(scope: Construct, id: string, props: StackProps & Icav2EventTranslatorStackProps) {
    super(scope, id);
    this.mainBus = EventBus.fromEventBusName(this, 'EventBus', props.eventBusName);
    this.vpc = Vpc.fromLookup(this, 'MainVpc', props.vpcProps);
    this.dynamoDBTable = TableV2.fromTableName(
      this,
      'Icav2EventTranslatorDynamoDBTable',
      props.icav2EventTranslatorDynamodbTableName
    );
    this.lambdaSG = SecurityGroup.fromLookupByName(
      this,
      'LambdaSecurityGroup',
      props.lambdaSecurityGroupName,
      this.vpc
    );

    this.createICAv2EventTranslator(props);
  }

  private createICAv2EventTranslator(props: Icav2EventTranslatorStackProps) {
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

    this.dynamoDBTable.grantReadWriteData(EventTranslatorFunction);

    // Create a rule to trigger the Lambda function from the EventBus ICAV2_EXTERNAL_EVENT
    const rule = new Rule(this, 'Rule', {
      eventBus: this.mainBus,
      eventPattern: {
        account: [Stack.of(this).account],
        detail: {
          'ica-event': {
            eventCode: ['ICA_EXEC_028'],
            projectId: [{ exists: true }],
            payload: {
              pipeline: {
                code: [{ prefix: 'BclConvert' }],
              },
            },
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
        resources: [this.mainBus.eventBusArn, this.dynamoDBTable.tableArn],
      })
    );
  }
}

/**
 * 
 * private createIcaEventTranslator(props: IcaEventPipeStackProps, IcaEventPipeName: string) {
    // extract the IcaEventTranslatorConstructProps
    const icaEventTranslatorProps = props.IcaEventTranslatorProps;

    const icaEventTranslatorConstructProps: Icav2EventTranslatorStackProps = {
      icav2EventTranslatorDynamodbTableName:
        icaEventTranslatorProps.icav2EventTranslatorDynamodbTableName,
      dynamodbTableRemovalPolicy: icaEventTranslatorProps.removalPolicy || RemovalPolicy.DESTROY, // default to destroy
      eventBusName: props.eventBusName,
      vpcProps: icaEventTranslatorProps.vpcProps,
      lambdaSecurityGroupName: icaEventTranslatorProps.lambdaSecurityGroupName,
      icaEventPipeName: IcaEventPipeName,
    };

    return new IcaEventTranslatorConstruct(
      this,
      'IcaEventTranslatorConstruct',
      icaEventTranslatorConstructProps
    );
  }
  */
