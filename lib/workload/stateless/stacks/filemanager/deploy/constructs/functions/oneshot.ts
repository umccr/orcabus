import { Construct } from 'constructs';
import { PolicyStatement, ServicePrincipal } from 'aws-cdk-lib/aws-iam';
import { Duration } from 'aws-cdk-lib';
import { IVpc, SecurityGroup, SubnetType } from 'aws-cdk-lib/aws-ec2';
import {
  AssetImage,
  Cluster,
  ContainerInsights,
  CpuArchitecture,
  FargateTaskDefinition,
  LogDriver,
} from 'aws-cdk-lib/aws-ecs';
import path from 'path';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Platform } from 'aws-cdk-lib/aws-ecr-assets';
import {
  ChainDefinitionBody,
  IntegrationPattern,
  JsonPath,
  Pass,
  StateMachine,
  Succeed,
  Timeout,
} from 'aws-cdk-lib/aws-stepfunctions';
import { EcsFargateLaunchTarget, EcsRunTask } from 'aws-cdk-lib/aws-stepfunctions-tasks';
import { Role } from './role';
import { RetentionDays } from 'aws-cdk-lib/aws-logs';
import { PostgresManagerStack } from '../../../../../../stateful/stacks/postgres-manager/deploy/stack';
import { FILEMANAGER_SERVICE_NAME } from '../../stack';

/**
 * Props for the oneshot API task.
 */
export type OneShotApiTaskProps = {
  /**
   * The buckets that the oneshot API task uses.
   */
  readonly buckets: string[];
  /**
   * Additional build environment variables when building the task.
   */
  readonly buildEnvironment?: { [key: string]: string };
  /**
   * Additional environment variables to set inside the task.
   */
  readonly environment?: { [key: string]: string };
  /**
   * RUST_LOG string, defaults to trace on local crates and info everywhere else.
   */
  readonly rustLog?: string;
  /**
   * The role which the task assumes.
   */
  readonly role?: iam.Role;
  /**
   * Vpc for the task.
   */
  readonly vpc: IVpc;
  /**
   * The length of time to keep logs for.
   */
  readonly logRetention?: RetentionDays;
};

/**
 * A construct for the oneshot API fargate task.
 */
export class OneShotApiTask extends Construct {
  readonly cluster: Cluster;
  readonly role: Role;

  constructor(scope: Construct, id: string, props: OneShotApiTaskProps) {
    super(scope, id);

    const role = props.role ?? new iam.Role(this, 'Role', {
      assumedBy: new ServicePrincipal('ecs-tasks.amazonaws.com'),
      description: 'Filemanager API oneshot fargate execution role',
      roleName: 'orcabus-filemanager-api-oneshot-role',
      maxSessionDuration: Duration.hours(12),
    });
    this.role = new Role(this, 'OneShotRole', {
      role
    });

    this.role.addCustomerManagedPolicy(
      PostgresManagerStack.formatRdsPolicyName(FILEMANAGER_SERVICE_NAME)
    );
    this.role.addPoliciesForBuckets(props.buckets, [
      ...Role.getObjectActions(),
      ...Role.getObjectVersionActions(),
      ...Role.objectTaggingActions(),
    ]);

    this.cluster = new Cluster(this, 'FargateCluster', {
      vpc: props.vpc,
      enableFargateCapacityProviders: true,
      containerInsightsV2: ContainerInsights.ENHANCED,
    });

    const name = 'orcabus-filemanager-api-oneshot-task';
    const taskDefinition = new FargateTaskDefinition(this, 'TaskDefinition', {
      runtimePlatform: {
        cpuArchitecture: CpuArchitecture.ARM64,
      },
      cpu: 256,
      memoryLimitMiB: 512,
      taskRole: props.role,
      family: name,
    });

    const entry = path.join(__dirname, '..', '..', '..');
    taskDefinition.addContainer('Container', {
      stopTimeout: Duration.seconds(120),
      image: new AssetImage(entry, {
        platform: Platform.LINUX_ARM64,
        buildArgs: {
          BINARY: 'filemanager-api-oneshot',
        }
      }),
      readonlyRootFilesystem: true,
      logging: LogDriver.awsLogs({
        streamPrefix: 'filemanager-api-oneshot',
        logRetention: props.logRetention,
      }),
    });
  }
}
