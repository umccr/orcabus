import * as cdk from 'aws-cdk-lib';
import { Match, Template } from 'aws-cdk-lib/assertions';
import { IcaEventPipeConstruct } from '../../../lib/workload/stateful/stacks/ica-event-pipe/constructs/ica_event_pipe';
import { IcaEventTranslatorConstruct } from '../../../lib/workload/stateful/stacks/ica-event-pipe/ica-event-translator/construct';
import { vpcProps } from '../../../config/constants';

const topicArn = 'arn:aws:sns:region-1:123456789123:TopicName';
const icaTestAccount = '123456789123';
let stack: cdk.Stack;

const app = new cdk.App();
beforeAll(() => {
  stack = new cdk.Stack();
});

describe('IcaEventPipeConstruct', () => {
  stack = new cdk.Stack(app, 'TestEventBusStackWithCustomArchiver', {
    env: { account: '123456789', region: 'ap-southeast-2' },
  });
  new IcaEventPipeConstruct(stack, 'TestIcaEventPipeConstruct', {
    icaEventPipeName: 'TestPipeName',
    icaQueueName: 'TestQueueName',
    icaQueueVizTimeout: 30,
    eventBusName: 'TestBus',
    slackTopicArn: topicArn,
    dlqMessageThreshold: 1,
    icaAwsAccountNumber: icaTestAccount,
  });

  new IcaEventTranslatorConstruct(stack, 'TestIcaEventTranslatorConstruct', {
    icav2EventTranslatorDynamodbTableName: 'TestDynamoDBTableName',
    dynamodbTableRemovalPolicy: cdk.RemovalPolicy.DESTROY,
    eventBusName: 'TestBus',
    vpcProps: vpcProps,
    lambdaSecurityGroupName: 'LambdaSecurityGroup',
    icaEventPipeName: 'TestPipeName',
  });

  const template = Template.fromStack(stack);
  // console.log(JSON.stringify(template, undefined, 2));

  test('SQS Queues created', () => {
    template.resourceCountIs('AWS::SQS::Queue', 2);
    template.hasResourceProperties('AWS::SQS::Queue', {
      QueueName: 'TestQueueName',
      RedrivePolicy: {
        deadLetterTargetArn: Match.anyValue(),
        maxReceiveCount: 3,
      },
    });

    template.hasResourceProperties('AWS::SQS::Queue', {
      QueueName: 'TestQueueName-dlq',
    });
  });

  test('SQS Queue configured with SSL', () => {
    // make sure all QueuePolicies enforce SSL
    template.resourceCountIs('AWS::SQS::QueuePolicy', 2);
    template.allResourcesProperties(
      'AWS::SQS::QueuePolicy',
      Match.objectLike({
        PolicyDocument: {
          Statement: Match.arrayWith([
            Match.objectLike({
              Action: 'sqs:*',
              Effect: 'Deny',
              Condition: {
                Bool: {
                  'aws:SecureTransport': 'false',
                },
              },
            }),
          ]),
        },
      })
    );
  });

  test('SQS Queue configured for ICA events', () => {
    template.hasResourceProperties(
      'AWS::SQS::QueuePolicy',
      Match.objectLike({
        PolicyDocument: {
          Statement: Match.arrayWith([
            Match.objectLike({
              Action: Match.arrayWith(['sqs:SendMessage']),
              Effect: 'Allow',
              Principal: {
                AWS: {
                  'Fn::Join': ['', ['arn:', Match.anyValue(), ':iam::' + icaTestAccount + ':root']],
                },
              },
            }),
          ]),
        },
      })
    );
  });

  test('CloudWatch Alarm created', () => {
    template.hasResourceProperties('AWS::CloudWatch::Alarm', {
      ComparisonOperator: 'GreaterThanOrEqualToThreshold',
      MetricName: 'ApproximateNumberOfMessagesVisible',
      Threshold: 1,
      AlarmActions: [topicArn],
      OKActions: [topicArn],
    });
  });

  test('Event Pipe with TargetInputTransformation created', () => {
    template.resourceCountIs('AWS::Pipes::Pipe', 1);
    template.hasResourceProperties('AWS::Pipes::Pipe', {
      TargetParameters: {
        InputTemplate: Match.anyValue(),
      },
    });
  });

  test('Event Translator Lambda created', () => {
    template.resourceCountIs('AWS::Lambda::Function', 1);
    template.hasResourceProperties('AWS::Lambda::Function', {
      Handler: 'icav2_event_translator.handler',
      Runtime: 'python3.12',
      Timeout: 28,
    });
  });

  test('Event Translator Lambda has permissions', () => {
    template.hasResourceProperties('AWS::IAM::Policy', {
      PolicyDocument: {
        Statement: Match.arrayWith([
          Match.objectLike({
            Action: ['events:PutEvents', 'dynamodb:PutItem', 'dynamodb:GetItem', 'dynamodb:Scan'],
            Resource: [Match.anyValue(), Match.anyValue()],
          }),
        ]),
      },
    });
  });

  test('Event Translator Rule created', () => {
    template.resourceCountIs('AWS::Events::Rule', 1);
    template.hasResourceProperties('AWS::Events::Rule', {
      EventPattern: {
        account: ['123456789'],
        'detail-type': ['Event from aws:sqs'],
        source: ['Pipe TestPipeName'],
        detail: {
          'ica-event': {
            eventCode: [{ prefix: 'ICA_EXEC_' }],
            projectId: [{ exists: true }],
            payload: [{ exists: true }],
          },
        },
      },
    });
  });

  test('DynamoDB Table created', () => {
    template.resourceCountIs('AWS::DynamoDB::GlobalTable', 1);
    template.hasResourceProperties('AWS::DynamoDB::GlobalTable', {
      TableName: 'TestDynamoDBTableName',
      AttributeDefinitions: [
        { AttributeName: 'analysis_id', AttributeType: 'S' },
        { AttributeName: 'event_status', AttributeType: 'S' },
      ],
    });
  });
});
