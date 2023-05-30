import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { getEnvironmentConfig } from '../../../config/constants';
import { EventBusConstruct } from '../../../lib/workload/stateful/eventbridge/component';

let stack: cdk.Stack;

const constructConfig = getEnvironmentConfig('beta');
if (!constructConfig) throw new Error('No construct config for the test');

beforeEach(() => {
  stack = new cdk.Stack();
});

test('Test EventBus Creation', () => {
  new EventBusConstruct(stack, 'TestEventBusConstruct', {
    ...constructConfig.stackProps.orcaBusStatefulConfig.eventBusProps,
  });
  const template = Template.fromStack(stack);

  template.hasResourceProperties('AWS::Events::EventBus', {
    Name: 'OrcaBusMain',
  });
});
