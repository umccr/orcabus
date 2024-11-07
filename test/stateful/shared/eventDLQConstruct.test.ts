import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { EventDLQConstruct } from '../../../lib/workload/stateful/stacks/shared/constructs/event-dlq';

let stack: cdk.Stack;

function assert_common(template: Template) {
  template.resourceCountIs('AWS::SQS::Queue', 1);

  template.hasResourceProperties('AWS::SQS::Queue', {
    QueueName: 'queue',
  });

  template.hasResourceProperties('AWS::CloudWatch::Alarm', {
    ComparisonOperator: 'GreaterThanThreshold',
    EvaluationPeriods: 1,
    Threshold: 0,
  });
}

beforeEach(() => {
  stack = new cdk.Stack();
});

test('Test EventSourceConstruct created props', () => {
  new EventDLQConstruct(stack, 'TestEventDLQConstruct', 'TestEventDLQAlarm', {
    queueName: 'queue',
    alarmName: 'alarm',
  });
  const template = Template.fromStack(stack);

  console.log(JSON.stringify(template, undefined, 2));

  assert_common(template);
});
