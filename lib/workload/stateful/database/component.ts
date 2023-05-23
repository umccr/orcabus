import { Construct } from 'constructs';
import { Aspects, RemovalPolicy } from 'aws-cdk-lib';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as ec2 from 'aws-cdk-lib/aws-ec2';

export interface DatabaseProps {
  clusterIdentifier: string;
  defaultDatabaseName: string;
  version: rds.AuroraMysqlEngineVersion;
  parameterGroupName: string;
  username: string;
}

export class DatabaseConstruct extends Construct {
  readonly dbSecurityGroup: ec2.SecurityGroup;
  readonly dbCluster: rds.DatabaseCluster;

  constructor(scope: Construct, id: string, vpc: ec2.IVpc, props: DatabaseProps) {
    super(scope, id);

    const secret = new rds.DatabaseSecret(this, id + 'Secret', {
      username: props.username,
    });

    this.dbSecurityGroup = new ec2.SecurityGroup(this, 'DbSecurityGroup', {
      vpc: vpc,
      allowAllOutbound: true,
    });

    this.dbCluster = new rds.DatabaseCluster(this, id + 'Cluster', {
      engine: rds.DatabaseClusterEngine.auroraMysql({
        version: props.version,
      }),
      instances: 1,
      instanceProps: {
        vpc: vpc,
        vpcSubnets: {
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
        },
        securityGroups: [this.dbSecurityGroup],
        instanceType: new ec2.InstanceType('serverless'),
        parameterGroup: rds.ParameterGroup.fromParameterGroupName(
          this,
          id + 'ParameterGroup',
          props.parameterGroupName
        ),
      },

      removalPolicy: RemovalPolicy.DESTROY,
      credentials: rds.Credentials.fromSecret(secret),
      clusterIdentifier: props.clusterIdentifier,
      defaultDatabaseName: props.defaultDatabaseName,
    });

    Aspects.of(this.dbCluster).add({
      visit(node) {
        if (node instanceof rds.CfnDBCluster) {
          node.serverlessV2ScalingConfiguration = {
            minCapacity: 0.5,
            maxCapacity: 1,
          };
        }
      },
    });
  }
}
