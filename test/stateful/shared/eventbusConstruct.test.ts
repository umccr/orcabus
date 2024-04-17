import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { getEnvironmentConfig } from '../../../config/config';
import { EventBusConstruct } from '../../../lib/workload/stateful/stacks/shared/constructs/event-bus';

let stack: cdk.Stack;

const constructConfig = getEnvironmentConfig('beta');
if (!constructConfig) throw new Error('No construct config for the test');

beforeEach(() => {
  stack = new cdk.Stack();
});

test('Test EventBusConstruct Creation', () => {
  new EventBusConstruct(
    stack,
    'TestEventBusConstruct',
    constructConfig.stackProps.statefulConfig.sharedStackProps.eventBusProps
  );
  const template = Template.fromStack(stack);

  template.hasResourceProperties('AWS::Events::EventBus', {
    Name: 'OrcaBusMain',
  });
});
