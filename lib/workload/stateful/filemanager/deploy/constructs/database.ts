import { Construct } from 'constructs';
import { IVpc, SecurityGroup, SubnetType } from 'aws-cdk-lib/aws-ec2';
import { ISecret } from 'aws-cdk-lib/aws-secretsmanager';
import {
  AuroraPostgresEngineVersion,
  ClusterInstance,
  DatabaseCluster,
  DatabaseClusterEngine,
} from 'aws-cdk-lib/aws-rds';
import { aws_ec2 as ec2, aws_rds as rds, Duration, RemovalPolicy } from 'aws-cdk-lib';
import { ManagedPolicy, Role, ServicePrincipal } from 'aws-cdk-lib/aws-iam';

/**
 * Props for enabling enhanced monitoring.
 */
export type EnableMonitoringProps = {
  /**
   * Add cloud watch exports.
   */
  readonly cloudwatchLogsExports?: string[];
  /**
   * Enable performance insights.
   */
  readonly enablePerformanceInsights?: boolean;
  /**
   * The interval for monitoring, defaults to 60 seconds.
   */
  readonly monitoringInterval?: Duration;
};

/**
 * Settable database props that can be configured.
 */
export type DatabaseSettings = {
  /**
   * Whether the database is publically available.
   */
  readonly public?: boolean;
  /**
   * Whether to destroy the database on stack removal. Defaults to keeping a snapshot.
   */
  readonly destroyOnRemove?: boolean;
  /**
   * Enable enhanced monitoring.
   */
  readonly enableMonitoring?: EnableMonitoringProps;
  /**
   * Minimum ACU capacity, defaults to 0.5.
   */
  readonly minCapacity?: number;
  /**
   * Maximum ACU capacity, defaults to 4.
   */
  readonly maxCapacity?: number;
  /**
   * Port to use for the database. The default for the engine is used if not specified.
   */
  readonly port?: number;
};

/**
 * Props for the database.
 */
export type DatabaseProps = DatabaseSettings & {
  /**
   * Vpc for the database.
   */
  readonly vpc: IVpc;
  /**
   * Secret for database credentials
   */
  readonly secret: ISecret;
  /**
   * The name of the database initially created.
   */
  readonly databaseName: string;
};

/**
 * A construct for the postgres database used with filemanager.
 */
export class Database extends Construct {
  private readonly _securityGroup: SecurityGroup;
  private readonly _cluster: DatabaseCluster;
  private readonly _unsafeConnection: string;

  constructor(scope: Construct, id: string, props: DatabaseProps) {
    super(scope, id);

    // Create security group with no outbound connections, because outbound connections
    // shouldn't be very useful for a database anyway.
    this._securityGroup = new SecurityGroup(this, 'SecurityGroup', {
      vpc: props.vpc,
      allowAllOutbound: false,
      allowAllIpv6Outbound: false,
      description: 'Security group for communicating with the filemanager RDS instance',
    });

    // Creates roles for enhanced RDS monitoring, if enabled.
    let enableMonitoring;
    if (props.enableMonitoring) {
      const monitoringRole = new Role(this, 'DatabaseMonitoringRole', {
        assumedBy: new ServicePrincipal('monitoring.rds.amazonaws.com'),
      });
      monitoringRole.addManagedPolicy(
        ManagedPolicy.fromAwsManagedPolicyName('service-role/AmazonRDSEnhancedMonitoringRole')
      );

      enableMonitoring = {
        enablePerformanceInsights: props.enableMonitoring.enablePerformanceInsights,
        cloudwatchLogsExports: props.enableMonitoring.cloudwatchLogsExports,
        monitoringInterval: props.enableMonitoring.monitoringInterval?.toSeconds() ?? 60,
        monitoringRoleArn: monitoringRole.roleArn,
      };
    }

    // Serverless V2 Cluster.
    this._cluster = new DatabaseCluster(this, 'Cluster', {
      vpc: props.vpc,
      vpcSubnets: {
        subnetType: props.public ? SubnetType.PUBLIC : SubnetType.PRIVATE_ISOLATED,
      },
      securityGroups: [this._securityGroup],
      credentials: rds.Credentials.fromSecret(props.secret),
      removalPolicy: props.destroyOnRemove ? RemovalPolicy.DESTROY : RemovalPolicy.SNAPSHOT,
      defaultDatabaseName: props.databaseName,
      port: props.port,
      engine: DatabaseClusterEngine.auroraPostgres({
        version: AuroraPostgresEngineVersion.VER_15_4,
      }),
      serverlessV2MinCapacity: props.minCapacity ?? 0.5,
      serverlessV2MaxCapacity: props.maxCapacity ?? 4,
      writer: ClusterInstance.serverlessV2('Writer', {
        ...(enableMonitoring && { ...enableMonitoring }),
      }),
    });

    // Any inbound connections within the same security group are allowed access to the database port.
    this._securityGroup.addIngressRule(
      this._securityGroup,
      ec2.Port.tcp(this._cluster.clusterEndpoint.port)
    );

    this._unsafeConnection =
      `postgres://` +
      `${props.secret.secretValueFromJson('username').unsafeUnwrap()}` +
      `:` +
      `${props.secret.secretValueFromJson('password').unsafeUnwrap()}` +
      `@` +
      `${this._cluster.clusterEndpoint.socketAddress}` +
      `/` +
      `${props.databaseName}`;
  }

  /**
   * Get the serverless cluster.
   */
  get cluster(): DatabaseCluster {
    return this._cluster;
  }

  /**
   * Get the security group for the database.
   */
  get securityGroup(): SecurityGroup {
    return this._securityGroup;
  }

  /**
   * Get the connection string. Unsafe because it contains the username and password.
   */
  get unsafeConnection(): string {
    return this._unsafeConnection;
  }
}
