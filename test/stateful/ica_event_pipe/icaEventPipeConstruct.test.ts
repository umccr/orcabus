import * as cdk from 'aws-cdk-lib';
import { Match, Template } from 'aws-cdk-lib/assertions';
import { IcaEventPipeConstruct } from '../../../lib/workload/stateful/stacks/ica_event_pipe/construct/ica_event_pipe';

const topicArn = 'arn:aws:sns:region-1:123456789123:TopicName';
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
    template.resourceCountIs('AWS::SQS::QueuePolicy', 2);
    template.hasResourceProperties('AWS::SQS::QueuePolicy', {
      PolicyDocument: Match.objectLike({
        Statement: [
          {
            Action: 'sqs:*',
            Effect: 'Deny',
            Condition: {
              Bool: {
                'aws:SecureTransport': 'false',
              },
            },
          },
        ],
      }),
    });
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
