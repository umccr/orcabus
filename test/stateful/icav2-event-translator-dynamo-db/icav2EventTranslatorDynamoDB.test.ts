import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { Icav2EventTranslatorTable } from '../../../lib/workload/stateful/stacks/icav2-event-translator-dynamo-db/deploy/stack';

let stack: cdk.Stack;

const app = new cdk.App();
beforeAll(() => {
  stack = new cdk.Stack();
});

describe('Icav2EventTranslatorTableStack', () => {
  stack = new cdk.Stack(app, 'TestEventBusStackWithCustomArchiver', {
    env: { account: '123456789', region: 'ap-southeast-2' },
  });
  new Icav2EventTranslatorTable(stack, 'TestIcav2EventTranslatorTableStack', {
    dynamodbTableName: 'TestDynamoDBTableName',
    removalPolicy: cdk.RemovalPolicy.DESTROY,
  });

  const template = Template.fromStack(stack);
  console.log(JSON.stringify(template, undefined, 2));

  test('DynamoDB Table created', () => {
    template.resourceCountIs('AWS::DynamoDB::GlobalTable', 1);
    template.hasResourceProperties('AWS::DynamoDB::GlobalTable', {
      TableName: 'TestDynamoDBTableName',
      AttributeDefinitions: [
        { AttributeName: 'id', AttributeType: 'S' },
        { AttributeName: 'id_type', AttributeType: 'S' },
      ],
    });
  });
});
