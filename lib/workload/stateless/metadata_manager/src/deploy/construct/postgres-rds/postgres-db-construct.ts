import { ISecurityGroup, IVpc, SecurityGroup } from 'aws-cdk-lib/aws-ec2';
import { ISecret } from 'aws-cdk-lib/aws-secretsmanager';
import { ServerlessCluster } from 'aws-cdk-lib/aws-rds';
import { Construct } from 'constructs';
import { aws_ec2 as ec2, aws_rds as rds, RemovalPolicy } from 'aws-cdk-lib';
import { BaseDatabase } from './base-database';
import { PostgresCommon } from './infrastructure-stack-database-props';

type ServerlessBaseDatabaseProps = PostgresCommon & {
  vpc: IVpc;

  databaseName: string;

  secret: ISecret;
};

/**
 * A construct representing the base database we might use with EdgeDb - in this
 * case representing a V2 Serverless Aurora (in postgres mode).
 */
export class ServerlessBaseDatabase extends BaseDatabase {
  private readonly _cluster: ServerlessCluster;
  private readonly _securityGroup: SecurityGroup;
  private readonly _dsnWithTokens: string;
  private readonly _dsnNoPassword: string;

  constructor(scope: Construct, id: string, props: ServerlessBaseDatabaseProps) {
    super(scope, id);

    // we create a security group and export its id - so we can use that as a security boundary
    // for services that "can connect to database"
    this._securityGroup = this.createMembershipSecurityGroup(props.vpc);

    this._cluster = new ServerlessCluster(this, 'ServerlessCluster', {
      vpc: props.vpc,
      securityGroups: [this._securityGroup],
      vpcSubnets: {
        subnetType: props.makePubliclyReachable
          ? ec2.SubnetType.PUBLIC
          : ec2.SubnetType.PRIVATE_WITH_EGRESS,
      },
      engine: rds.DatabaseClusterEngine.auroraPostgres({
        version: rds.AuroraPostgresEngineVersion.VER_14_7,
      }),
      // the default database to create in the cluster - we insist on it being named otherwise no default db is made
      defaultDatabaseName: props.databaseName,
      credentials: rds.Credentials.fromSecret(props.secret),
      // destroy on remove tells us we don't really care much about the data (demo instances etc)
      removalPolicy: props.destroyOnRemove ? RemovalPolicy.DESTROY : RemovalPolicy.SNAPSHOT,
    });

    // temporary fix to broken CDK constructs
    // https://github.com/aws/aws-cdk/issues/20197#issuecomment-1272360016
    {
      const cfnDBCluster = this._cluster.node.children.find(
        (node) => node instanceof rds.CfnDBCluster
      ) as rds.CfnDBCluster;
      cfnDBCluster.serverlessV2ScalingConfiguration = {
        minCapacity: props.minCapacity ?? 0.5,
        maxCapacity: props.maxCapacity ?? rds.AuroraCapacityUnit.ACU_4,
      };
      cfnDBCluster.engineMode = undefined;
    }

    let enableMonitoring;
    if (props.enableMonitoring) {
      const monitoringRole = this.createMonitoringRole();

      enableMonitoring = {
        enablePerformanceInsights: props.enableMonitoring.enablePerformanceInsights,
        cloudwatchLogsExports: props.enableMonitoring.cloudwatchLogsExports,
        monitoringInterval: props.enableMonitoring.monitoringInterval.toSeconds(),
        monitoringRoleArn: monitoringRole.roleArn,
      };
    }

    new rds.CfnDBInstance(this, 'Writer', {
      dbInstanceClass: 'db.serverless',
      dbClusterIdentifier: this._cluster.clusterIdentifier,
      engine: 'aurora-postgresql',
      publiclyAccessible: props.makePubliclyReachable,
      ...(enableMonitoring && { ...enableMonitoring }),
    });

    this.applySecurityGroupRules(
      this._securityGroup,
      this._cluster.clusterEndpoint.port,
      props.makePubliclyReachable
    );

    this._dsnWithTokens =
      `postgres://` +
      `${props.secret.secretValueFromJson('username').unsafeUnwrap()}` +
      `:` +
      `${props.secret.secretValueFromJson('password').unsafeUnwrap()}` +
      `@` +
      `${this._cluster.clusterEndpoint.hostname}` +
      `:` +
      `${this._cluster.clusterEndpoint.port}` +
      `/` +
      `${props.databaseName}`;

    this._dsnNoPassword =
      `postgres://` +
      `${props.adminUser}@${this._cluster.clusterEndpoint.hostname}:${this._cluster.clusterEndpoint.port}/${props.databaseName}`;
  }

  public get dsnWithTokens(): string {
    return this._dsnWithTokens;
  }

  public get dsnNoPassword(): string {
    return this._dsnNoPassword;
  }

  public get hostname(): string {
    return this._cluster.clusterEndpoint.hostname;
  }

  public get port(): number {
    return this._cluster.clusterEndpoint.port;
  }

  public get securityGroup(): ISecurityGroup {
    return this._securityGroup;
  }
}
