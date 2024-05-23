import { Construct } from 'constructs';
import { Duration, Stack, StackProps } from 'aws-cdk-lib';
import { TableV2 } from 'aws-cdk-lib/aws-dynamodb';
import { EventBus, Rule, IEventBus } from 'aws-cdk-lib/aws-events';
import { Runtime, Architecture } from 'aws-cdk-lib/aws-lambda';
import { PythonFunction, PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import { Vpc, VpcLookupOptions, SecurityGroup } from 'aws-cdk-lib/aws-ec2';
import { LambdaFunction } from 'aws-cdk-lib/aws-events-targets';
import { PolicyStatement } from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as path from 'path';

export interface BclConvertManagerStackProps {
  /** dynamodb name and event bus name */
  icav2EventTranslatorDynamodbTableName: string;
  eventBusName: string;
  /** vpc ann SG for lambda function */
  vpcProps: VpcLookupOptions;
  lambdaSecurityGroupName: string;
}

export class BclConvertManagerStack extends Stack {
  private readonly lambdaRuntimePythonVersion = Runtime.PYTHON_3_12;

  constructor(scope: Construct, id: string, props: StackProps & BclConvertManagerStackProps) {
    super(scope, id, props);

    // Create the ICAv2 Event Translator service
    this.createICAv2EventTranslator(props);
  }

  private createICAv2EventTranslator(props: BclConvertManagerStackProps) {
    const mainBus = EventBus.fromEventBusName(this, 'EventBus', props.eventBusName);
    const vpc = Vpc.fromLookup(this, 'MainVpc', props.vpcProps);
    const dynamoDBTable = TableV2.fromTableName(
      this,
      'Icav2EventTranslatorDynamoDBTable',
      props.icav2EventTranslatorDynamodbTableName
    );

    const lambdaSG = new SecurityGroup(this, 'IcaEventTranslatorLambdaSG', {
      vpc,
      securityGroupName: props.lambdaSecurityGroupName,
      allowAllOutbound: true,
      description:
        'Security group that allows teh Ica Event Translator (BclConvertManager) function to egress out.',
    });

    const EventTranslatorFunction = new PythonFunction(this, 'EventTranslator', {
      entry: path.join(__dirname, '../translator_service'),
      runtime: this.lambdaRuntimePythonVersion,
      environment: {
        TABLE_NAME: props.icav2EventTranslatorDynamodbTableName,
        EVENT_BUS_NAME: props.eventBusName,
      },
      vpc: vpc,
      vpcSubnets: { subnets: vpc.privateSubnets },
      securityGroups: [lambdaSG],
      architecture: Architecture.ARM_64,
      timeout: Duration.seconds(28),
      index: 'icav2_event_translator.py',
      handler: 'handler',
    });

    dynamoDBTable.grantReadWriteData(EventTranslatorFunction);

    // Create a rule to trigger the Lambda function from the EventBus ICAV2_EXTERNAL_EVENT
    const rule = new Rule(this, 'Rule', {
      eventBus: mainBus,
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
        actions: ['events:PutEvents'],
        resources: [mainBus.eventBusArn],
      })
    );
  }
}
