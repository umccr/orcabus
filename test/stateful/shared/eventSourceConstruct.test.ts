import * as cdk from 'aws-cdk-lib';
import { Match, Template } from 'aws-cdk-lib/assertions';
import { EventSourceConstruct } from '../../../lib/workload/stateful/stacks/shared/constructs/event-source';
import { getEventSourceConstructProps } from '../../../config/stacks/shared';
import { EventBridge } from '@aws-sdk/client-eventbridge';
import { AppStage, oncoanalyserBucket } from '../../../config/constants';

let stack: cdk.Stack;
let eventbridge: EventBridge;

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

/**
 * Test the event against the pattern.
 */
async function testEventPattern(event: any, pattern: any): Promise<boolean | undefined> {
  const request = await eventbridge.testEventPattern({
    Event: JSON.stringify(event),
    EventPattern: JSON.stringify(pattern),
  });
  return request.Result;
}

function testS3Event(bucket: string, key: string, size: number): any {
  return {
    version: '0',
    id: '17793124-05d4-b198-2fde-7ededc63b103',
    'detail-type': 'Object Created',
    source: 'aws.s3',
    account: '111122223333',
    time: '2021-11-12T00:00:00Z',
    region: 'ca-central-1',
    resources: [`arn:aws:s3:::${bucket}`],
    detail: {
      version: '0',
      bucket: {
        name: bucket,
      },
      object: {
        key: key,
        size: size,
        etag: 'b1946ac92492d2347c6235b4d2611184', // pragma: allowlist secret
        'version-id': 'IYV3p45BT0ac8hjHg1houSdS1a.Mro8e',
        sequencer: '617f08299329d189', // pragma: allowlist secret
      },
      'request-id': 'N4N7GDK58NMKJ12R',
      requester: '123456789012',
      'source-ip-address': '1.2.3.4',
      reason: 'PutObject',
    },
  };
}

beforeEach(() => {
  stack = new cdk.Stack();
  eventbridge = new EventBridge();
});

test.only('Test event source event patterns', async () => {
  new EventSourceConstruct(
    stack,
    'TestEventSourceConstruct',
    getEventSourceConstructProps(AppStage.BETA)
  );

  const template = Template.fromStack(stack);

  const pattern = Object.entries(template.findResources('AWS::Events::Rule'))[0][1]['Properties'][
    'EventPattern'
  ];
  const event = testS3Event(oncoanalyserBucket[AppStage.BETA], 'example-key', 1);

  // Not a directory and size is greater than 0
  expect(await testEventPattern(event, pattern)).toBe(true);

  // Not a directory and size is 0
  event['detail']['object']['key'] = 'example-key';
  event['detail']['object']['size'] = 0;
  expect(await testEventPattern(event, pattern)).toBe(true);

  // Is a directory but size is greater than 0
  event['detail']['object']['key'] = 'example-key/';
  event['detail']['object']['size'] = 1;
  expect(await testEventPattern(event, pattern)).toBe(true);

  // Is a directory and size is 0. This should be the only one that gets filtered out.
  event['detail']['object']['key'] = 'example-key/';
  event['detail']['object']['size'] = 0;
  expect(await testEventPattern(event, pattern)).toBe(false);
});

test('Test EventSourceConstruct created props', () => {
  new EventSourceConstruct(stack, 'TestEventSourceConstruct', {
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

test('Test EventSourceConstruct created props with event types', () => {
  new EventSourceConstruct(stack, 'TestEventSourceConstruct', {
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

test('Test EventSourceConstruct created props with key rule', () => {
  new EventSourceConstruct(stack, 'TestEventSourceConstruct', {
    queueName: 'queue',
    maxReceiveCount: 100,
    rules: [
      {
        bucket: 'bucket',
        patterns: { key: [{ 'anything-but': { wildcard: 'wildcard/*' } }, { prefix: 'prefix' }] },
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
              'anything-but': { wildcard: 'wildcard/*' },
            },
            {
              prefix: 'prefix',
            },
          ],
        },
      },
    },
  });
});

test('Test EventSourceConstruct created props with rules matching any bucket', () => {
  new EventSourceConstruct(stack, 'TestEventSourceConstruct', {
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
