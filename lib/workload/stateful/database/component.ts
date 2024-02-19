import { Construct } from 'constructs';
import { RemovalPolicy, Duration } from 'aws-cdk-lib';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { SecurityGroup } from 'aws-cdk-lib/aws-ec2';
import { DatabaseCluster } from 'aws-cdk-lib/aws-rds';

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
export type ConfigurableDatabaseProps = MonitoringProps & {
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
};

/**
 * Database props with vpc and inbound security group.
 */
export type DatabaseProps = ConfigurableDatabaseProps & {
  /**
   * The database VPC.
   */
  vpc: ec2.IVpc;
  /**
   * Inbound security group for the database.
   */
  allowedInboundSG?: ec2.SecurityGroup;
};

export class Database extends Construct {
  readonly securityGroup: SecurityGroup;
  readonly cluster: DatabaseCluster;

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
  }
}
