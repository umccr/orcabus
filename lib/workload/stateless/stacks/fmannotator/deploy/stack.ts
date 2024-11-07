import { Arn, aws_events_targets as targets, Duration, Stack, StackProps } from 'aws-cdk-lib';
import {
  ISecurityGroup,
  IVpc,
  SecurityGroup,
  SubnetType,
  Vpc,
  VpcLookupOptions,
} from 'aws-cdk-lib/aws-ec2';
import { Construct } from 'constructs';
import { GoFunction } from '@aws-cdk/aws-lambda-go-alpha';
import path from 'path';
import { Architecture } from 'aws-cdk-lib/aws-lambda';
import { EventBus, IEventBus, Rule } from 'aws-cdk-lib/aws-events';
import { Secret } from 'aws-cdk-lib/aws-secretsmanager';
import { NamedLambdaRole } from '../../../../components/named-lambda-role';
import { ManagedPolicy, PolicyStatement, Role } from 'aws-cdk-lib/aws-iam';
import { IQueue, Queue } from 'aws-cdk-lib/aws-sqs';

/**
 * Config for the FM annotator.
 */
export type FMAnnotatorConfig = {
  vpcProps: VpcLookupOptions;
  eventBusName: string;
  eventDLQName: string;
  jwtSecretName: string;
};

/**
 * Props for the FM annotator stack which can be configured
 */
export type FMAnnotatorConfigurableProps = StackProps & FMAnnotatorConfig;

/**
 * Props for the FM annotator stack.
 */
export type FMAnnotatorProps = FMAnnotatorConfigurableProps & {
  domainName: string;
};

/**
 * Construct used to configure the FM annotator.
 */
export class FMAnnotator extends Stack {
  private readonly vpc: IVpc;
  private readonly securityGroup: ISecurityGroup;
  private readonly eventBus: IEventBus;
  private readonly role: Role;
  private readonly dlq: IQueue;

  constructor(scope: Construct, id: string, props: FMAnnotatorProps) {
    super(scope, id, props);

    this.vpc = Vpc.fromLookup(this, 'MainVpc', props.vpcProps);
    this.eventBus = EventBus.fromEventBusName(this, 'OrcaBusMain', props.eventBusName);

    this.securityGroup = new SecurityGroup(this, 'SecurityGroup', {
      vpc: this.vpc,
      allowAllOutbound: true,
      description: 'Security group that allows the annotator Lambda to egress out.',
    });

    const tokenSecret = Secret.fromSecretNameV2(this, 'JwtSecret', props.jwtSecretName);

    this.role = new NamedLambdaRole(this, 'Role');
    this.addAwsManagedPolicy('service-role/AWSLambdaVPCAccessExecutionRole');
    // Need access to secrets to fetch FM JWT token.
    tokenSecret.grantRead(this.role);

    this.dlq = Queue.fromQueueArn(
      this,
      'FilemanagerQueue',
      Arn.format(
        {
          resource: props.eventDLQName,
          service: 'sqs',
        },
        this
      )
    );

    const env = {
      FMANNOTATOR_FILE_MANAGER_ENDPOINT: `https://${props.domainName}`,
      FMANNOTATOR_FILE_MANAGER_SECRET_NAME: tokenSecret.secretName,
      FMANNOTATOR_QUEUE_NAME: this.dlq.queueName,
      FMANNOTATOR_QUEUE_MAX_MESSAGES: '100',
      FMANNOTATOR_QUEUE_WAIT_TIME_SECS: '60',
      GO_LOG: 'debug',
    };
    const entry = path.join(__dirname, '..', 'cmd', 'portalrunid');
    const fn = new GoFunction(this, 'PortalRunId', {
      entry,
      environment: env,
      memorySize: 128,
      timeout: Duration.seconds(28),
      architecture: Architecture.ARM_64,
      role: this.role,
      vpc: this.vpc,
      vpcSubnets: { subnetType: SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [this.securityGroup],
      deadLetterQueue: this.dlq,
      deadLetterQueueEnabled: true,
    });

    const eventRule = new Rule(this, 'EventRule', {
      description: 'Send WorkflowRunStateChange events to the annotator Lambda',
      eventBus: this.eventBus,
    });

    eventRule.addTarget(new targets.LambdaFunction(fn));
    eventRule.addEventPattern({
      // Allow accepting a self-made event used for testing.
      source: ['orcabus.workflowmanager', 'orcabus.fmannotator'],
      detailType: ['WorkflowRunStateChange'],
      detail: {
        status: [
          { 'equals-ignore-case': 'SUCCEEDED' },
          { 'equals-ignore-case': 'FAILED' },
          { 'equals-ignore-case': 'ABORTED' },
        ],
      },
    });

    const entryQueue = path.join(__dirname, '..', 'cmd', 'portalrunidqueue');
    new GoFunction(this, 'PortalRunIdQueue', {
      entry: entryQueue,
      environment: env,
      memorySize: 128,
      timeout: Duration.seconds(28),
      architecture: Architecture.ARM_64,
      role: this.role,
      vpc: this.vpc,
      vpcSubnets: { subnetType: SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [this.securityGroup],
      deadLetterQueue: this.dlq,
      deadLetterQueueEnabled: true,
    });
  }

  /**
   * Add an AWS managed policy to the function's role.
   */
  addAwsManagedPolicy(policyName: string) {
    this.role.addManagedPolicy(ManagedPolicy.fromAwsManagedPolicyName(policyName));
  }

  /**
   * Add a policy statement to this function's role.
   */
  addToPolicy(policyStatement: PolicyStatement) {
    this.role.addToPolicy(policyStatement);
  }
}
