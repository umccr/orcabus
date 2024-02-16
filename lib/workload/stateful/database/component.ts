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
   * performance insights retention period.
   */
  readonly performanceInsightsRetention?: rds.PerformanceInsightRetention;
  /**
   * Enable enhanced monitoring by specifying the interval.
   */
  readonly enhancedMonitoringInterval?: Duration;
};

/**
 * Database props without a VPC.
 */
export type DatabasePropsNoVPC = MonitoringProps & {
  /**
   * The cluster identifier.
   */
  clusterIdentifier: string;
  /**
   * The initial database name created.
   */
  defaultDatabaseName: string;
  /**
   * Parameter group for the database.
   */
  parameterGroupName: string;
  /**
   * Database username.
   */
  username: string;
  /**
   * Database secret name.
   */
  masterSecretName: string;
  /**
   * Database engine version.
   */
  version: rds.AuroraPostgresEngineVersion;
  /**
   * Number of database instances.
   */
  numberOfInstance: number;
  /**
   * Min ACU for serverless database.
   */
  minACU: number;
  /**
   * Max ACU for serverless database.
   */
  maxACU: number;
  /**
   * Port to run the database on.
   */
  dbPort: number;
  /**
   * The database removal policy.
   */
  removalPolicy: RemovalPolicy;
  /**
   * Inbound security groups that are allowed to connect to the database.
   */
  allowedInboundSG?: ec2.SecurityGroup;
};

/**
 * Database props with a vpc.
 */
export type DatabaseProps = DatabasePropsNoVPC & {
  /**
   * The database VPC.
   */
  vpc: ec2.IVpc;
};

/**
 * Interface representing the database.
 */
export interface IDatabase {
  /**
   * The database security group.
   */
  readonly securityGroup: ec2.SecurityGroup;
  /**
   * The database cluster.
   */
  readonly cluster: rds.DatabaseCluster;
  /**
   * A connection string to the database.
   */
  readonly unsafeConnection: string;
}

export class Database extends Construct implements IDatabase {
  readonly securityGroup: ec2.SecurityGroup;
  readonly cluster: rds.DatabaseCluster;
  readonly unsafeConnection: string;

  constructor(scope: Construct, id: string, props: DatabaseProps) {
    super(scope, id);

    const dbSecret = new rds.DatabaseSecret(this, id + 'DbSecret', {
      username: props.username,
      secretName: props.masterSecretName,
    });

    this.securityGroup = new ec2.SecurityGroup(this, 'DbSecurityGroup', {
      vpc: props.vpc,
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
      storageEncrypted: true,
      iamAuthentication: true,
      removalPolicy: props.removalPolicy,
      securityGroups: [this.securityGroup],
      serverlessV2MaxCapacity: props.maxACU,
      serverlessV2MinCapacity: props.minACU,
      vpc: props.vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
      },

      cloudwatchLogsExports: props.cloudwatchLogsExports,
      monitoringInterval: props.enhancedMonitoringInterval,

      writer: rds.ClusterInstance.serverlessV2('WriterClusterInstance', {
        enablePerformanceInsights: props.enablePerformanceInsights,
      }),
    });

    // Todo use secrets manager for this and query for password within Lambda functions.
    this.unsafeConnection =
      `postgres://` +
      `${dbSecret.secretValueFromJson('username').unsafeUnwrap()}` +
      `:` +
      `${dbSecret.secretValueFromJson('password').unsafeUnwrap()}` +
      `@` +
      `${this.cluster.clusterEndpoint.socketAddress}` +
      `/` +
      `${props.defaultDatabaseName}`;
  }
}
