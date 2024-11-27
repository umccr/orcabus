import { Duration, Stack, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import path from 'path';
import { ISecurityGroup, IVpc, SecurityGroup, Vpc, VpcLookupOptions } from 'aws-cdk-lib/aws-ec2';
import { PolicyStatement, Role, ServicePrincipal } from 'aws-cdk-lib/aws-iam';
import {
  AssetImage,
  Cluster,
  ContainerDefinition,
  CpuArchitecture,
  FargateTaskDefinition,
  LogDriver,
} from 'aws-cdk-lib/aws-ecs';
import { Platform } from 'aws-cdk-lib/aws-ecr-assets';
import { LogGroup, RetentionDays } from 'aws-cdk-lib/aws-logs';
import { EcsFargateLaunchTarget, EcsRunTask } from 'aws-cdk-lib/aws-stepfunctions-tasks';
import { IntegrationPattern } from 'aws-cdk-lib/aws-stepfunctions';

/**
 * Props for the data migrate stack.
 */
export type DataMigrateStackProps = {
  /**
   * Props to lookup the VPC with.
   */
  vpcProps: VpcLookupOptions;
  /**
   * The name of the role for the data mover.
   */
  dataMoverRoleName?: string;
  /**
   * Define the buckets that the mover is allowed to read from.
   */
  readFromBuckets: string[];
  /**
   * Define the buckets that the mover is allowed to write to.
   */
  writeToBuckets: string[];
  /**
   * Define the buckets that the mover is allowed to delete from after copying.
   */
  deleteFromBuckets: string[];
  /**
   * How long to keep logs for.
   */
  logRetention: RetentionDays;
};

/**
 * Deploy the data migrate stack.
 */
export class DataMigrateStack extends Stack {
  private readonly vpc: IVpc;
  private readonly role: Role;
  private readonly cluster: Cluster;

  constructor(scope: Construct, id: string, props: StackProps & DataMigrateStackProps) {
    super(scope, id, props);

    this.role = new Role(this, 'Role', {
      assumedBy: new ServicePrincipal('ecs-tasks.amazonaws.com'),
      description: props?.description ?? 'Fargate execution role',
      roleName: props?.dataMoverRoleName,
      maxSessionDuration: Duration.hours(12),
    });
    this.addPoliciesForBuckets(this.role, props.readFromBuckets, [
      's3:ListBucket',
      's3:GetObject',
      's3:GetObjectVersion',
      's3:GetObjectTagging',
      's3:GetObjectVersionTagging',
    ]);
    this.addPoliciesForBuckets(this.role, props.writeToBuckets, ['s3:PutObject']);
    this.addPoliciesForBuckets(this.role, props.deleteFromBuckets, ['s3:DeleteObject']);

    this.vpc = Vpc.fromLookup(this, 'MainVpc', props.vpcProps);
    this.cluster = new Cluster(this, 'FargateCluster', {
      vpc: this.vpc,
      enableFargateCapacityProviders: true,
    });

    const entry = path.join(__dirname, '..');
    const taskDefinition = new FargateTaskDefinition(this, 'TaskDefinition', {
      runtimePlatform: {
        cpuArchitecture: CpuArchitecture.X86_64,
      },
      cpu: 256,
      memoryLimitMiB: 1024,
      taskRole: this.role,
      family: 'orcabus-data-migrate-mover',
    });
    const container = taskDefinition.addContainer('DataMoverContainer', {
      stopTimeout: Duration.seconds(120),
      image: new AssetImage(entry, {
        platform: Platform.LINUX_AMD64,
      }),
      readonlyRootFilesystem: true,
      logging: LogDriver.awsLogs({
        streamPrefix: 'data-migrate',
        logRetention: props.logRetention,
      }),
    });

    const securityGroup = new SecurityGroup(this, 'SecurityGroup', {
      vpc: this.vpc,
      allowAllOutbound: true,
      description: 'Security group that allows a filemanager Lambda function to egress out.',
    });

    new EcsRunTask(this, 'Run the data mover', {
      cluster: this.cluster,
      taskDefinition: taskDefinition,
      launchTarget: EcsFargateLaunchTarget,
      securityGroups: {},
      subnets: {
        subnetType: props.vpcSubnetSelection,
      },
      resultPath: '$.dataMoverResult',
      containerOverrides: [
        {
          containerDefinition: container,
        },
      ],
    });
  }

  /**
   * Add policies to the role.
   */
  addPoliciesForBuckets(role: Role, buckets: string[], actions: string[]) {
    buckets.map((bucket) => {
      role.addToPolicy(
        new PolicyStatement({
          actions,
          resources: [`arn:aws:s3:::${bucket}`, `arn:aws:s3:::${bucket}/*`],
        })
      );
    });
  }
}
