import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { getEnvironmentConfig } from '../../../config/config';
import { SchemaRegistryConstruct } from '../../../lib/workload/stateful/stacks/shared/constructs/schema-registry';

let stack: cdk.Stack;

const constructConfig = getEnvironmentConfig('beta');
if (!constructConfig) throw new Error('No construct config for the test');

beforeEach(() => {
  stack = new cdk.Stack();
});

test('Test SchemaRegistryConstruct Creation', () => {
  new SchemaRegistryConstruct(
    stack,
    'TestSchemaRegistryConstruct',
    constructConfig.stackProps.statefulConfig.sharedStackProps.schemaRegistryProps
  );
  const template = Template.fromStack(stack);

  template.hasResourceProperties('AWS::EventSchemas::Registry', {
    RegistryName: 'OrcaBusSchemaRegistry',
  });
});
