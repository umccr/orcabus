import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { DynamodbIcav2PipelineConstruct } from '../../../lib/workload/components/dynamodb-icav2-table';

let stack: cdk.Stack;

const app = new cdk.App();
beforeAll(() => {
  stack = new cdk.Stack();
});

describe('Icav2EventTranslatorTableStack', () => {
  stack = new cdk.Stack(app, 'TestIcav2EventTranslatorTable', {
    env: { account: '123456789', region: 'ap-southeast-2' },
  });
  new DynamodbIcav2PipelineConstruct(stack, 'TestIcav2EventTranslatorTableStack', {
    tableName: 'TestDynamoDBTableName',
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
