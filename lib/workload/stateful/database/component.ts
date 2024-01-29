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
  version: rds.AuroraPostgresEngineVersion;
  numberOfInstance: number;
  minACU: number;
  maxACU: number;
  dbPort: number;
  allowedInboundSG?: ec2.SecurityGroup;
};

export class DatabaseConstruct extends Construct {
  readonly dbSecurityGroup: ec2.SecurityGroup;
  readonly dbCluster: rds.DatabaseCluster;

  constructor(scope: Construct, id: string, vpc: ec2.IVpc, props: DatabaseProps) {
    super(scope, id);

    const dbSecret = new rds.DatabaseSecret(this, id + 'DbSecret', {
      username: props.username,
    });

    this.dbSecurityGroup = new ec2.SecurityGroup(this, 'DbSecurityGroup', {
      vpc: vpc,
      allowAllOutbound: false,
      allowAllIpv6Outbound: false,
      description: 'security group for OrcaBus RDS',
    });

    // give compute sg to access the rds
    if (props.allowedInboundSG) {
      this.dbSecurityGroup.addIngressRule(
        props.allowedInboundSG,
        ec2.Port.tcp(props.dbPort),
        'allow the OrcaBus compute sg to access db'
      );
    }

    this.dbCluster = new rds.DatabaseCluster(this, id + 'Cluster', {
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
      securityGroups: [this.dbSecurityGroup],
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
  }
}
