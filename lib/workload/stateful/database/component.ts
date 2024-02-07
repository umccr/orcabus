import { Construct } from 'constructs';
import { RemovalPolicy, Duration } from 'aws-cdk-lib';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as ec2 from 'aws-cdk-lib/aws-ec2';

/**
 * Props for enabling enhanced monitoring.
 */
type MonitoringProps = {
  /**
   * Add cloud watch exports.
   */
  readonly cloudwatchLogsExports?: string[];
  /**
   * Enable performance insights.
   */
  readonly enablePerformanceInsights?: boolean;
  /**
   * performance insights retention period
   */
  readonly performanceInsightsRetention?: rds.PerformanceInsightRetention;
  /**
   * Enable enhanced monitoring by specifying the interval
   */
  readonly enhancedMonitoringInterval?: Duration;
};

export type DatabaseProps = MonitoringProps & {
  clusterIdentifier: string;
  defaultDatabaseName: string;
  parameterGroupName: string;
  username: string;
  masterSecretName: string;
  version: rds.AuroraPostgresEngineVersion;
  numberOfInstance: number;
  minACU: number;
  maxACU: number;
  dbPort: number;
  allowedInboundSG?: ec2.SecurityGroup;
};

export interface IDatabase {
  readonly securityGroup: ec2.SecurityGroup;
  readonly cluster: rds.DatabaseCluster;
  readonly unsafeConnection: string;
}

export class Database extends Construct implements IDatabase {
  readonly securityGroup: ec2.SecurityGroup;
  readonly cluster: rds.DatabaseCluster;
  readonly unsafeConnection: string;

  constructor(scope: Construct, id: string, vpc: ec2.IVpc, props: DatabaseProps) {
    super(scope, id);

    const dbSecret = new rds.DatabaseSecret(this, id + 'DbSecret', {
      username: props.username,
      secretName: props.masterSecretName,
    });

    this.securityGroup = new ec2.SecurityGroup(this, 'DbSecurityGroup', {
      vpc: vpc,
      allowAllOutbound: false,
      allowAllIpv6Outbound: false,
      description: 'security group for OrcaBus RDS',
    });

    // give compute sg to access the rds
    if (props.allowedInboundSG) {
      this.securityGroup.addIngressRule(
        props.allowedInboundSG,
        ec2.Port.tcp(props.dbPort),
        'allow the OrcaBus compute sg to access db'
      );
    }

    this.cluster = new rds.DatabaseCluster(this, id + 'Cluster', {
      engine: rds.DatabaseClusterEngine.auroraPostgres({ version: props.version }),
      clusterIdentifier: props.clusterIdentifier,
      credentials: rds.Credentials.fromSecret(dbSecret),
      defaultDatabaseName: props.defaultDatabaseName,
      parameterGroup: rds.ParameterGroup.fromParameterGroupName(
        this,
        id + 'ParameterGroup',
        props.parameterGroupName
      ),
      port: props.dbPort,
      removalPolicy: RemovalPolicy.DESTROY,
      securityGroups: [this.securityGroup],
      serverlessV2MaxCapacity: props.maxACU,
      serverlessV2MinCapacity: props.minACU,
      vpc: vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
      },

      cloudwatchLogsExports: props.cloudwatchLogsExports,
      monitoringInterval: props.enhancedMonitoringInterval,

      writer: rds.ClusterInstance.serverlessV2('WriterClusterInstance', {
        enablePerformanceInsights: props.enablePerformanceInsights,
      }),
    });

    this.unsafeConnection =
      `postgres://` +
      `${props.secret.secretValueFromJson('username').unsafeUnwrap()}` +
      `:` +
      `${props.secret.secretValueFromJson('password').unsafeUnwrap()}` +
      `@` +
      `${this._cluster.clusterEndpoint.socketAddress}` +
      `/` +
      `${props.databaseName}`;
  }
}
