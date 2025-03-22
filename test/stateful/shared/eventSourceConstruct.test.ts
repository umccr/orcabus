import * as cdk from 'aws-cdk-lib';
import { Match, Template } from 'aws-cdk-lib/assertions';
import { EventSourceConstruct } from '../../../lib/workload/stateful/stacks/shared/constructs/event-source';
import { getEventSourceConstructProps } from '../../../config/stacks/shared';
import { EventBridge } from '@aws-sdk/client-eventbridge';
import {
  AppStage,
  icav2ArchiveAnalysisBucket,
  icav2ArchiveFastqBucket,
  icav2PipelineCacheBucket,
  oncoanalyserBucket,
} from '../../../config/constants';

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

async function test_directory_objects(event: any, pattern: any) {
  event['detail']['object']['key'] = 'example-key/';
  event['detail']['object']['size'] = 0;
  expect(await testEventPattern(event, pattern)).toBe(false);

  event['detail']['object']['key'] = 'example-key';
  event['detail']['object']['size'] = 0;
  expect(await testEventPattern(event, pattern)).toBe(true);

  event['detail']['object']['key'] = '/';
  event['detail']['object']['size'] = 0;
  expect(await testEventPattern(event, pattern)).toBe(false);

  event['detail']['object']['key'] = 'example-key/';
  event['detail']['object']['size'] = 1;
  expect(await testEventPattern(event, pattern)).toBe(true);

  event['detail']['object']['key'] = 'example-key';
  event['detail']['object']['size'] = 1;
  expect(await testEventPattern(event, pattern)).toBe(true);

  event['detail']['object']['key'] = '/';
  event['detail']['object']['size'] = 1;
  expect(await testEventPattern(event, pattern)).toBe(true);
}

test.only('Test event source event patterns', async () => {
  new EventSourceConstruct(
    stack,
    'TestEventSourceConstruct',
    getEventSourceConstructProps(AppStage.PROD)
  );

  const template = Template.fromStack(stack);

  let pattern = Object.entries(template.findResources('AWS::Events::Rule'))[0][1]['Properties'][
    'EventPattern'
  ];
  let event = testS3Event(oncoanalyserBucket[AppStage.PROD], 'example-key', 1);
  await test_directory_objects(event, pattern);

  pattern = Object.entries(template.findResources('AWS::Events::Rule'))[1][1]['Properties'][
    'EventPattern'
  ];
  event = testS3Event(icav2PipelineCacheBucket[AppStage.PROD], 'example-key', 1);
  await test_directory_objects(event, pattern);
  // The cache bucket should additionally ignore cache objects.
  event['detail']['object']['key'] = 'byob-icav2/123/cache/123';
  event['detail']['object']['size'] = 0;
  expect(await testEventPattern(event, pattern)).toBe(false);

  event['detail']['object']['key'] = 'byob-icav2/123/cache/123/';
  event['detail']['object']['size'] = 0;
  expect(await testEventPattern(event, pattern)).toBe(false);

  event['detail']['object']['key'] = 'byob-icav2/123/cache/123';
  event['detail']['object']['size'] = 1;
  expect(await testEventPattern(event, pattern)).toBe(false);

  event['detail']['object']['key'] = 'byob-icav2/123/cache/123/';
  event['detail']['object']['size'] = 1;
  expect(await testEventPattern(event, pattern)).toBe(false);

  pattern = Object.entries(template.findResources('AWS::Events::Rule'))[2][1]['Properties'][
    'EventPattern'
  ];
  event = testS3Event(icav2ArchiveAnalysisBucket[AppStage.PROD], 'example-key', 1);
  await test_directory_objects(event, pattern);

  pattern = Object.entries(template.findResources('AWS::Events::Rule'))[3][1]['Properties'][
    'EventPattern'
  ];
  event = testS3Event(icav2ArchiveFastqBucket[AppStage.PROD], 'example-key', 1);
  await test_directory_objects(event, pattern);
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
