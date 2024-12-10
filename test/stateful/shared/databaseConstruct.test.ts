import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { DatabaseConstruct } from '../../../lib/workload/stateful/stacks/shared/constructs/database';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { getEnvironmentConfig } from '../../../config/config';
import { AppStage } from '../../../config/constants';

let stack: cdk.Stack;
let vpc: ec2.Vpc;

const constructConfig = getEnvironmentConfig(AppStage.BETA);
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
  new DatabaseConstruct(stack, 'TestDatabaseConstruct', {
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

  new DatabaseConstruct(stack, 'TestDatabaseConstruct', {
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

test('Test tier-2 backup created for DBCluster and it is compliance in production configuration', () => {
  const prodConfig = getEnvironmentConfig(AppStage.PROD);
  if (!prodConfig) throw new Error('No construct config for the test');

  expect(prodConfig).toBeTruthy();
  const dbProps = prodConfig.stackProps.statefulConfig.sharedStackProps.databaseProps;

  new DatabaseConstruct(stack, 'TestDatabaseConstruct', {
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

  // Assert that we are compliance with long term tier-2 backup plan

  template.hasResource('AWS::Backup::BackupVault', {
    DeletionPolicy: 'Retain',
  });
  template.hasResourceProperties('AWS::Backup::BackupVault', {
    BackupVaultName: 'OrcaBusDatabaseTier2BackupVault',
  });

  template.hasResource('AWS::Backup::BackupPlan', {
    DeletionPolicy: 'Retain',
  });
  template.hasResourceProperties('AWS::Backup::BackupPlan', {
    BackupPlan: {
      BackupPlanName: 'OrcaBusDatabaseTier2BackupPlan',
      BackupPlanRule: [
        {
          Lifecycle: {
            DeleteAfterDays: 42,
          },
          RuleName: 'Weekly',
          ScheduleExpression: 'cron(0 17 ? * SUN *)',
        },
      ],
    },
  });
});
