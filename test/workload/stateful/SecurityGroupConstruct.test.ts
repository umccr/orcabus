import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Template } from 'aws-cdk-lib/assertions';
import { getEnvironmentConfig } from '../../../config/constants';
import { SecurityGroupConstruct } from '../../../lib/workload/stateful/securitygroup/component';

let stack: cdk.Stack;
let vpc: ec2.Vpc;

const constructConfig = getEnvironmentConfig('beta');
if (!constructConfig) throw new Error('No construct config for the test');

beforeEach(() => {
  stack = new cdk.Stack();
  vpc = new ec2.Vpc(stack, 'MockExistingVPC', {
    subnetConfiguration: [{ name: 'privateSubnet', subnetType: ec2.SubnetType.PRIVATE_ISOLATED }],
  });
});

test('Test SchemaRegistry Creation', () => {
  new SecurityGroupConstruct(stack, 'TestSGConstruct', vpc, {
    ...constructConfig.stackProps.orcaBusStatefulConfig.securityGroupProps,
  });
  const template = Template.fromStack(stack);

  template.hasResourceProperties('AWS::EC2::SecurityGroup', {
    GroaupName: 'OrcaBusLambdaSecurityGroup',
  });
});
