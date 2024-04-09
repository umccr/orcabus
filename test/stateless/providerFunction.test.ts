import * as cdk from 'aws-cdk-lib';
import { Match, Template } from 'aws-cdk-lib/assertions';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Function, Runtime, S3Code } from 'aws-cdk-lib/aws-lambda';
import { ProviderFunction } from '../../lib/workload/components/provider_function';
import { Bucket } from 'aws-cdk-lib/aws-s3';

let stack: cdk.Stack;
let vpc: ec2.Vpc;

beforeEach(() => {
  stack = new cdk.Stack();
  vpc = new ec2.Vpc(stack, 'MockExistingVPC', {
    subnetConfiguration: [
      {
        cidrMask: 24,
        name: 'publicSubnet',
        subnetType: ec2.SubnetType.PUBLIC,
      },
      {
        cidrMask: 24,
        name: 'privateWithEgressSubnet',
        subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
      },
    ],
  });
});

function assert_common(template: Template, key: string) {
  // Contains the provider.
  template.hasResourceProperties('AWS::Lambda::Function', {
    Environment: {
      Variables: {
        USER_ON_EVENT_FUNCTION_ARN: {
          'Fn::GetAtt': [Match.stringLikeRegexp('TestFunction*'), 'Arn'],
        },
      },
    },
  });

  // Contains the custom resource.
  template.hasResourceProperties('AWS::CloudFormation::CustomResource', {
    S3Key: key,
  });
}

test('Test ProviderFunction', () => {
  const testFunction = new Function(stack, 'TestFunction', {
    code: new S3Code(new Bucket(stack, 'TestBucket', { bucketName: 'bucket' }), 'key'),
    runtime: Runtime.NODEJS_20_X,
    handler: 'index.handler',
  });

  new ProviderFunction(stack, 'TestProviderFunction', {
    function: testFunction,
    vpc,
  });

  const template = Template.fromStack(stack);
  assert_common(template, 'key');
});

test('Test ProviderFunction additionalHash', () => {
  const testFunction = new Function(stack, 'TestFunction', {
    code: new S3Code(new Bucket(stack, 'TestBucket', { bucketName: 'bucket' }), 'key'),
    runtime: Runtime.NODEJS_20_X,
    handler: 'index.handler',
  });

  new ProviderFunction(stack, 'TestProviderFunction', {
    function: testFunction,
    vpc,
    additionalHash: 'hash',
  });

  const template = Template.fromStack(stack);
  assert_common(template, 'hash');
});

test('Test ProviderFunction properties', () => {
  const testFunction = new Function(stack, 'TestFunction', {
    code: new S3Code(new Bucket(stack, 'TestBucket', { bucketName: 'bucket' }), 'key'),
    runtime: Runtime.NODEJS_20_X,
    handler: 'index.handler',
  });

  new ProviderFunction(stack, 'TestProviderFunction', {
    function: testFunction,
    vpc,
    resourceProperties: { Property: 'value' },
  });

  const template = Template.fromStack(stack);
  assert_common(template, 'key');

  template.hasResourceProperties('AWS::CloudFormation::CustomResource', {
    Property: 'value',
  });
});
