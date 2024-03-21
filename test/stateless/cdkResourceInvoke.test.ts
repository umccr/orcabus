import * as cdk from 'aws-cdk-lib';
import { Match, Template } from 'aws-cdk-lib/assertions';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { CdkResourceInvoke } from '../../lib/workload/components/cdk_resource_invoke';

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

test('Test CdkResourceInvoke', () => {
  new CdkResourceInvoke(stack, 'TestCdkResourceInvoke', {
    functionProps: {
      code: new lambda.InlineCode('exports.handler = async (event) => console.log(event)'),
      runtime: lambda.Runtime.NODEJS_20_X,
      handler: 'index.handler',
    },
    id: 'TestFunction',
    vpc,
    createFunction: (scope, id, props) => {
      return new lambda.Function(scope, id, props);
    },
  });
  const template = Template.fromStack(stack);

  const expectedHash = '7a1920d61156abc05a60135a'; // pragma: allowlist secret

  // Contains the Lambda function.
  template.hasResourceProperties('AWS::Lambda::Function', {
    Code: {
      ZipFile: 'exports.handler = async (event) => console.log(event)',
    },
    FunctionName: `${expectedHash}-ResourceInvokeFunction-TestFunction`,
    Handler: 'index.handler',
    Runtime: 'nodejs20.x',
  });

  // Has policy to invoke it.
  template.hasResourceProperties('AWS::IAM::Policy', {
    PolicyDocument: {
      Statement: [
        {
          Action: 'lambda:InvokeFunction',
          Effect: 'Allow',
          Resource: {
            'Fn::Join': [
              '',
              Match.arrayWith([`:function:${expectedHash}-ResourceInvokeFunction-*`]),
            ],
          },
        },
      ],
    },
  });
});
