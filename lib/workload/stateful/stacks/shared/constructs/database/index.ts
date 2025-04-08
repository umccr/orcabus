import { Construct } from 'constructs';
import { RemovalPolicy, Duration } from 'aws-cdk-lib';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as sm from 'aws-cdk-lib/aws-secretsmanager';
import * as backup from 'aws-cdk-lib/aws-backup';
import * as events from 'aws-cdk-lib/aws-events';
import { SecurityGroup } from 'aws-cdk-lib/aws-ec2';
import { DatabaseCluster } from 'aws-cdk-lib/aws-rds';

/**
 * Props for enabling enhanced monitoring.
 */
type MonitoringProps = {
  /**
   * Add cloud watch exports.
   */
  cloudwatchLogsExports?: string[];
  /**
   * Enable performance insights.
   */
  enablePerformanceInsights?: boolean;
  /**
   * performance insights retention period.
   */
  performanceInsightsRetention?: rds.PerformanceInsightRetention;
  /**
   * Enable enhanced monitoring by specifying the interval.
   */
  enhancedMonitoringInterval?: Duration;
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
  /**
   * Tier 1 backup - using built-in RDS system capability
   *
   * RDS aurora automated backup retention (in Duration)
   */
  backupRetention: Duration;
  /**
   * Tier 2 backup - leveraging another AWS Backup service is intentional redundancy
   *
   * Create long term tier-2 RDS aurora backup using AWS Backup service (in boolean)
   */
  createT2BackupRetention?: boolean;
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

export class DatabaseConstruct extends Construct {
  readonly securityGroup: SecurityGroup;
  readonly cluster: DatabaseCluster;

  constructor(scope: Construct, id: string, props: DatabaseProps) {
    super(scope, id);

    const dbSecret = new rds.DatabaseSecret(this, 'DbSecret', {
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

    this.cluster = new rds.DatabaseCluster(this, 'Cluster', {
      engine: rds.DatabaseClusterEngine.auroraPostgres({ version: props.version }),
      clusterIdentifier: props.clusterIdentifier,
      credentials: rds.Credentials.fromSecret(dbSecret),
      defaultDatabaseName: props.defaultDatabaseName,
      parameterGroup: rds.ParameterGroup.fromParameterGroupName(
        this,
        'ParameterGroup',
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

      backup: {
        retention: props.backupRetention,
      },
      enableDataApi: true,
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

    /**
     * See compliance rule
     * https://trello.com/c/RFnECxRa
     * https://github.com/umccr/orcabus/issues/178
     *
     * Backup weekly and keep it for 6 weeks
     * Cron At 17:00 on every Sunday UTC = AEST/AEDT 3AM/4AM on every Monday
     * cron(0 17 ? * SUN *)
     */
    if (props.createT2BackupRetention) {
      const t2BackupVault = new backup.BackupVault(this, 'OrcaBusDatabaseTier2BackupVault', {
        backupVaultName: 'OrcaBusDatabaseTier2BackupVault',
        removalPolicy: RemovalPolicy.RETAIN,
      });

      const t2BackupPlan = new backup.BackupPlan(this, 'OrcaBusDatabaseTier2BackupPlan', {
        backupPlanName: 'OrcaBusDatabaseTier2BackupPlan',
        backupVault: t2BackupVault,
      });
      t2BackupPlan.applyRemovalPolicy(RemovalPolicy.RETAIN);

      // https://github.com/aws/aws-cdk/blob/main/packages/aws-cdk-lib/aws-backup/lib/rule.ts
      t2BackupPlan.addRule(
        new backup.BackupPlanRule({
          ruleName: 'Weekly',
          scheduleExpression: events.Schedule.cron({
            hour: '17',
            minute: '0',
            weekDay: 'SUN',
          }),
          deleteAfter: Duration.days(42),
        })
      );

      t2BackupPlan.addSelection('OrcaBusDatabaseTier2BackupSelection', {
        resources: [backup.BackupResource.fromRdsServerlessCluster(this.cluster)],
      });
    }
  }
}
