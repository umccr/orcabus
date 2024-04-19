import * as cdk from 'aws-cdk-lib';
import { AccountPrincipal } from 'aws-cdk-lib/aws-iam';
import { Match, Template } from 'aws-cdk-lib/assertions';
import { IcaEventPipeConstruct } from '../../../lib/workload/stateful/stacks/ica-event-pipe/constructs/ica_event_pipe';

const topicArn = 'arn:aws:sns:region-1:123456789123:TopicName';
const icaTestAccount = '123456789123';
let stack: cdk.Stack;

beforeAll(() => {
  stack = new cdk.Stack();
});

describe('IcaEventPipeConstruct', () => {
  stack = new cdk.Stack();
  new IcaEventPipeConstruct(stack, 'TestIcaEventPipeConstruct', {
    icaEventPipeName: 'TestPipeName',
    icaQueueName: 'TestQueueName',
    icaQueueVizTimeout: 30,
    eventBusName: 'TestBus',
    slackTopicArn: topicArn,
    dlqMessageThreshold: 1,
    icaAwsAccountNumber: icaTestAccount,
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
});
