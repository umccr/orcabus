import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { Database } from '../../../lib/workload/stateful/stacks/shared/constructs/database';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { getEnvironmentConfig } from '../../../config/constants';

let stack: cdk.Stack;
let vpc: ec2.Vpc;

const constructConfig = getEnvironmentConfig('beta');
if (!constructConfig) throw new Error('No construct config for the test');

expect(constructConfig).toBeTruthy();
const dbProps = constructConfig.stackProps.statefulConfig.sharedStackProps.databaseProps;

beforeEach(() => {
  stack = new cdk.Stack();
  vpc = new ec2.Vpc(stack, 'MockExistingVPC', {
    subnetConfiguration: [
      { name: 'isolated', subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
      { name: 'privateWithEgress', subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      { name: 'public', subnetType: ec2.SubnetType.PUBLIC },
    ],
  });
});

test('Test DBCluster created props', () => {
  new Database(stack, 'TestDatabaseConstruct', {
    vpc,
    ...dbProps,
  });
  const template = Template.fromStack(stack);

  template.hasResourceProperties('AWS::RDS::DBCluster', {
    DBClusterIdentifier: 'orcabus-db',
    DatabaseName: 'orcabus',
    DBClusterParameterGroupName: dbProps.parameterGroupName,
    ServerlessV2ScalingConfiguration: {
      MaxCapacity: dbProps.maxACU,
      MinCapacity: dbProps.minACU,
    },
  });
});

test('Test other SG Allow Ingress to DB SG', () => {
  const allowedSG = new ec2.SecurityGroup(stack, 'AllowedSG', {
    securityGroupName: 'Allowed DB Ingress',
    vpc,
  });
  const sgLogicalId = stack.getLogicalId(allowedSG.node.defaultChild as ec2.CfnSecurityGroup);

  new Database(stack, 'TestDatabaseConstruct', {
    vpc,
    allowedInboundSG: allowedSG,
    ...dbProps,
  });
  const template = Template.fromStack(stack);

  template.hasResourceProperties('AWS::EC2::SecurityGroupIngress', {
    ToPort: dbProps.dbPort,
    FromPort: dbProps.dbPort,
    SourceSecurityGroupId: {
      'Fn::GetAtt': [sgLogicalId, 'GroupId'],
    },
  });
});
