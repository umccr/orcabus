import * as cdk from 'aws-cdk-lib';
import { Match, Template } from 'aws-cdk-lib/assertions';
import { EventSource } from '../../../lib/workload/stateful/stacks/shared/constructs/event_source';

let stack: cdk.Stack;

function assert_common(template: Template) {
  template.resourceCountIs('AWS::SQS::Queue', 2);

  template.hasResourceProperties('AWS::SQS::Queue', {
    QueueName: 'queue',
    RedrivePolicy: {
      deadLetterTargetArn: Match.anyValue(),
      maxReceiveCount: 100,
    },
  });

  template.hasResourceProperties('AWS::CloudWatch::Alarm', {
    ComparisonOperator: 'GreaterThanThreshold',
    EvaluationPeriods: 1,
    Threshold: 0,
  });

  template.hasResourceProperties('AWS::Events::Rule', {
    EventPattern: {
      source: ['aws.s3'],
      detail: {
        bucket: {
          name: ['bucket'],
        },
      },
    },
  });
}

beforeEach(() => {
  stack = new cdk.Stack();
});

test('Test EventSource created props', () => {
  new EventSource(stack, 'TestEventSourceConstruct', {
    queueName: 'queue',
    maxReceiveCount: 100,
    rules: [
      {
        bucket: 'bucket',
      },
    ],
  });
  const template = Template.fromStack(stack);

  console.log(JSON.stringify(template, undefined, 2));

  assert_common(template);
});

test('Test EventSource created props with event types', () => {
  new EventSource(stack, 'TestEventSourceConstruct', {
    queueName: 'queue',
    maxReceiveCount: 100,
    rules: [
      {
        bucket: 'bucket',
        eventTypes: ['Object Created'],
      },
    ],
  });
  const template = Template.fromStack(stack);

  assert_common(template);
  template.hasResourceProperties('AWS::Events::Rule', {
    EventPattern: {
      'detail-type': ['Object Created'],
    },
  });
});

test('Test EventSource created props with prefix', () => {
  new EventSource(stack, 'TestEventSourceConstruct', {
    queueName: 'queue',
    maxReceiveCount: 100,
    rules: [
      {
        bucket: 'bucket',
        prefix: 'prefix',
      },
    ],
  });
  const template = Template.fromStack(stack);

  assert_common(template);
  template.hasResourceProperties('AWS::Events::Rule', {
    EventPattern: {
      detail: {
        object: {
          key: [
            {
              prefix: 'prefix',
            },
          ],
        },
      },
    },
  });
});

test('Test EventSource created props with rules matching any bucket', () => {
  new EventSource(stack, 'TestEventSourceConstruct', {
    queueName: 'queue',
    maxReceiveCount: 100,
    rules: [{}],
  });
  const template = Template.fromStack(stack);

  template.hasResourceProperties('AWS::Events::Rule', {
    EventPattern: {
      source: ['aws.s3'],
      detail: {},
    },
  });
});
