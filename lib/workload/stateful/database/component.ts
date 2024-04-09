import { Construct } from 'constructs';
import { RemovalPolicy, Duration } from 'aws-cdk-lib';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as sm from 'aws-cdk-lib/aws-secretsmanager';
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
  /**
   * The ssm parameter name to store the cluster resource id.
   */
  clusterResourceIdParameterName: string;
  /**
   * The ssm parameter name to store the cluster endpoint
   */
  clusterEndpointHostParameterName: string;
  /**
   * The schedule (in Duration) that will rotate the master secret
   */
  secretRotationSchedule: Duration;
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

    new sm.SecretRotation(this, 'MasterDbSecretRotation', {
      application: sm.SecretRotationApplication.POSTGRES_ROTATION_SINGLE_USER,
      // From default: https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_rds.DatabaseSecret.html#excludecharacters
      excludeCharacters: '" %+~`#$&()|[]{}:;' + `<>?!'/@"\\")*`,
      secret: dbSecret,
      target: this.cluster,
      automaticallyAfter: props.secretRotationSchedule,
      securityGroup: props.allowedInboundSG,
      vpc: props.vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
      },
    });

    // saving the cluster id to be used in stateless stack on rds-iam
    // ref: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/UsingWithRDS.IAMDBAuth.IAMPolicy.html
    new ssm.StringParameter(this, 'DbClusterResourceIdSSM', {
      stringValue: this.cluster.clusterResourceIdentifier,
      description: 'cluster resource id at the orcabus rds cluster',
      parameterName: props.clusterResourceIdParameterName,
    });

    // Save the endpoint so that it can be used by the stateless services.
    new ssm.StringParameter(this, 'DbClusterEndpointHostSSM', {
      stringValue: this.cluster.clusterEndpoint.hostname,
      description: 'orcabus rds writer cluster endpoint host',
      parameterName: props.clusterEndpointHostParameterName,
    });
  }
}
