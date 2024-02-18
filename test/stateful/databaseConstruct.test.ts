import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { Database } from '../../lib/workload/stateful/database/component';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { getEnvironmentConfig } from '../../config/constants';

let stack: cdk.Stack;
let vpc: ec2.Vpc;

const constructConfig = getEnvironmentConfig('beta');
if (!constructConfig) throw new Error('No construct config for the test');

expect(constructConfig).toBeTruthy();
const dbProps = constructConfig.stackProps.orcaBusStatefulConfig.databaseProps;

beforeEach(() => {
  stack = new cdk.Stack();
  vpc = new ec2.Vpc(stack, 'MockExistingVPC', {
    subnetConfiguration: [{ name: 'privateSubnet', subnetType: ec2.SubnetType.PRIVATE_ISOLATED }],
  });
});

test('Test DBCluster created props', () => {
  new Database(stack, 'TestDatabaseConstruct', {
    vpc,
    ...constructConfig.stackProps.orcaBusStatefulConfig.databaseProps,
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
  const props = constructConfig.stackProps.orcaBusStatefulConfig.databaseProps;
  props.inboundSecurityGroupName = 'test-security-group';
  const database = new Database(stack, 'TestDatabaseConstruct', {
    vpc,
    ...props,
  });

  const sgLogicalId = stack.getLogicalId(
    database.inboundSecurityGroup.node.defaultChild as ec2.CfnSecurityGroup
  );

  const template = Template.fromStack(stack);
  console.log(JSON.stringify(template, undefined, 2));

  template.hasResourceProperties('AWS::EC2::SecurityGroupIngress', {
    ToPort: dbProps.dbPort,
    FromPort: dbProps.dbPort,
    SourceSecurityGroupId: {
      'Fn::GetAtt': [sgLogicalId, 'GroupId'],
    },
  });

  template.hasResourceProperties('AWS::EC2::SecurityGroup', {
    GroupName: props.inboundSecurityGroupName,
  });
});
