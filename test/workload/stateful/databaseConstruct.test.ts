import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { DatabaseConstruct } from '../../../lib/workload/stateful/database/component';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { getEnvironmentConfig } from '../../../config/constants';

let stack: cdk.Stack;
let vpc: ec2.Vpc;

const constructConfig = getEnvironmentConfig('beta');
expect(constructConfig).toBeTruthy();

beforeEach(() => {
  stack = new cdk.Stack();
  vpc = new ec2.Vpc(stack, 'MockExistingVPC', {
    subnetConfiguration: [{ name: 'privateSubnet', subnetType: ec2.SubnetType.PRIVATE_ISOLATED }],
  });
});

test('Test DBCluster created props', () => {
  new DatabaseConstruct(stack, 'TestDatabaseConstruct', vpc, {
    ...constructConfig!.stackProps.orcaBusStatefulConfig.databaseProps,
  });
  const template = Template.fromStack(stack);

  template.hasResourceProperties('AWS::RDS::DBCluster', {
    DBClusterIdentifier: 'orcabus-db',
    DatabaseName: 'orcabus',
    DBClusterParameterGroupName: 'default.aurora-mysql8.0',
    ServerlessV2ScalingConfiguration: {
      MaxCapacity: 1,
      MinCapacity: 0.5,
    },
  });
});

test('Test other SG Allow Ingress to DB SG', () => {
  const allowedSG = new ec2.SecurityGroup(stack, 'AllowedSG', {
    securityGroupName: 'Allowed DB Ingress',
    vpc,
  });
  const sgLogicalId = stack.getLogicalId(allowedSG.node.defaultChild as ec2.CfnSecurityGroup);

  new DatabaseConstruct(stack, 'TestDatabaseConstruct', vpc, {
    ...constructConfig!.stackProps.orcaBusStatefulConfig.databaseProps,
    allowDbSGIngressRule: [{ peer: allowedSG, description: 'Allowed SG DB Ingress' }],
  });
  const template = Template.fromStack(stack);

  template.hasResourceProperties('AWS::EC2::SecurityGroupIngress', {
    ToPort: 3306,
    FromPort: 3306,
    SourceSecurityGroupId: {
      'Fn::GetAtt': [sgLogicalId, 'GroupId'],
    },
  });
});
