import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { getEnvironmentConfig } from '../../../config/config';
import { SchemaRegistryConstruct } from '../../../lib/workload/stateful/stacks/shared/constructs/schema-registry';
import {
  AppStage,
  dataSchemaRegistryName,
  eventSchemaRegistryName,
} from '../../../config/constants';

let stack: cdk.Stack;

const constructConfig = getEnvironmentConfig(AppStage.BETA);
if (!constructConfig) throw new Error('No construct config for the test');

beforeEach(() => {
  stack = new cdk.Stack();
});

test('Test orcabus.events SchemaRegistryConstruct Creation', () => {
  new SchemaRegistryConstruct(
    stack,
    'TestEventSchemaRegistryConstruct',
    constructConfig.stackProps.statefulConfig.sharedStackProps.eventSchemaRegistryProps
  );
  const template = Template.fromStack(stack);

  template.hasResourceProperties('AWS::EventSchemas::Registry', {
    RegistryName: eventSchemaRegistryName,
  });
});

test('Test orcabus.data SchemaRegistryConstruct Creation', () => {
  new SchemaRegistryConstruct(
    stack,
    'TestDataSchemaRegistryConstruct',
    constructConfig.stackProps.statefulConfig.sharedStackProps.dataSchemaRegistryProps
  );
  const template = Template.fromStack(stack);

  template.hasResourceProperties('AWS::EventSchemas::Registry', {
    RegistryName: dataSchemaRegistryName,
  });
});
