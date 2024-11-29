import { Duration, Stack, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import path from 'path';
import { IVpc, SecurityGroup, SubnetType, Vpc, VpcLookupOptions } from 'aws-cdk-lib/aws-ec2';
import { PolicyStatement, Role, ServicePrincipal } from 'aws-cdk-lib/aws-iam';
import {
  AssetImage,
  Cluster,
  CpuArchitecture,
  FargateTaskDefinition,
  LogDriver,
} from 'aws-cdk-lib/aws-ecs';
import { Platform } from 'aws-cdk-lib/aws-ecr-assets';
import { RetentionDays } from 'aws-cdk-lib/aws-logs';
import { EcsFargateLaunchTarget, EcsRunTask } from 'aws-cdk-lib/aws-stepfunctions-tasks';
import {
  ChainDefinitionBody,
  IntegrationPattern,
  JsonPath,
  Pass,
  StateMachine,
  Succeed,
  Timeout,
} from 'aws-cdk-lib/aws-stepfunctions';
import { startExecution } from 'aws-cdk-lib/custom-resources/lib/provider-framework/runtime/outbound';

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
    this.role.addToPolicy(
      new PolicyStatement({
        resources: ['*'],
        actions: ['states:SendTaskSuccess', 'states:SendTaskFailure', 'states:SendTaskHeartbeat'],
      })
    );

    this.addPoliciesForBuckets(this.role, props.readFromBuckets, [
      's3:ListBucket',
      's3:GetObject',
      's3:GetObjectVersion',
      's3:GetObjectTagging',
      's3:GetObjectVersionTagging',
    ]);
    this.addPoliciesForBuckets(this.role, props.writeToBuckets, [
      's3:PutObject',
      's3:PutObjectTagging',
      's3:PutObjectVersionTagging',
      // The bucket being written to also needs to be listed for sync to work.
      's3:ListBucket',
    ]);
    this.addPoliciesForBuckets(this.role, props.deleteFromBuckets, ['s3:DeleteObject']);

    this.vpc = Vpc.fromLookup(this, 'MainVpc', props.vpcProps);
    this.cluster = new Cluster(this, 'FargateCluster', {
      vpc: this.vpc,
      enableFargateCapacityProviders: true,
      containerInsights: true,
    });

    const entry = path.join(__dirname, '..');
    const name = 'orcabus-data-migrate-mover';
    const taskDefinition = new FargateTaskDefinition(this, 'TaskDefinition', {
      runtimePlatform: {
        cpuArchitecture: CpuArchitecture.ARM64,
      },
      cpu: 256,
      memoryLimitMiB: 1024,
      taskRole: this.role,
      family: name,
    });
    const container = taskDefinition.addContainer('DataMoverContainer', {
      stopTimeout: Duration.seconds(120),
      image: new AssetImage(entry, {
        platform: Platform.LINUX_ARM64,
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
    });

    const startState = new Pass(this, 'StartState');
    const getCommand = new Pass(this, 'GetCommand', {
      parameters: {
        commands: JsonPath.array(
          JsonPath.stringAt('$.command'),
          '--source',
          JsonPath.stringAt('$.source'),
          '--destination',
          JsonPath.stringAt('$.destination')
        ),
      },
    });
    // Todo take input from ArchiveData event portalRunId as command.
    const task = new EcsRunTask(this, 'RunDataMover', {
      cluster: this.cluster,
      taskTimeout: Timeout.duration(Duration.hours(12)),
      integrationPattern: IntegrationPattern.WAIT_FOR_TASK_TOKEN,
      taskDefinition: taskDefinition,
      launchTarget: new EcsFargateLaunchTarget(),
      securityGroups: [securityGroup],
      subnets: {
        subnetType: SubnetType.PRIVATE_WITH_EGRESS,
      },
      containerOverrides: [
        {
          containerDefinition: container,
          command: JsonPath.listAt('$.commands'),
          environment: [
            {
              name: 'DM_TASK_TOKEN',
              value: JsonPath.stringAt('$$.Task.Token'),
            },
          ],
        },
      ],
    });
    // Todo output a complete event.
    const finish = new Succeed(this, 'SuccessState');

    new StateMachine(this, 'StateMachine', {
      stateMachineName: name,
      definitionBody: ChainDefinitionBody.fromChainable(
        startState.next(getCommand).next(task).next(finish)
      ),
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
