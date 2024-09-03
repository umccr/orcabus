import { aws_events_targets as targets, Duration, Stack, StackProps } from 'aws-cdk-lib';
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
import { ISecret } from 'aws-cdk-lib/aws-secretsmanager';
import { NamedLambdaRole } from '../../../../components/named-lambda-role';
import { ManagedPolicy, PolicyStatement, Role } from 'aws-cdk-lib/aws-iam';

/**
 * Config for the FM annotator.
 */
export type FMAnnotatorConfig = {
  vpcProps: VpcLookupOptions;
  eventBusName: string;
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
  secret: ISecret;
};

/**
 * Construct used to configure the FM annotator.
 */
export class FMAnnotator extends Stack {
  private readonly vpc: IVpc;
  private readonly securityGroup: ISecurityGroup;
  private readonly eventBus: IEventBus;
  private readonly role: Role;

  constructor(scope: Construct, id: string, props: FMAnnotatorProps) {
    super(scope, id, props);

    this.vpc = Vpc.fromLookup(this, 'MainVpc', props.vpcProps);
    this.eventBus = EventBus.fromEventBusName(this, 'OrcaBusMain', props.eventBusName);

    this.securityGroup = new SecurityGroup(this, 'SecurityGroup', {
      vpc: this.vpc,
      allowAllOutbound: true,
      description: 'Security group that allows the annotator Lambda to egress out.',
    });

    this.role = new NamedLambdaRole(this, 'Role');
    this.addAwsManagedPolicy('service-role/AWSLambdaVPCAccessExecutionRole');
    // Need access to secrets to fetch FM JWT token.
    this.addToPolicy(
      new PolicyStatement({
        actions: ['secretsmanager:DescribeSecret', 'secretsmanager:GetSecretValue'],
        resources: [props.secret.secretArn],
      })
    );

    const entry = path.join(__dirname, '..');
    const fn = new GoFunction(this, 'handler', {
      entry,
      environment: {
        FMANNOTATOR_FILE_MANAGER_ENDPOINT: props.domainName,
        FMANNOTATOR_FILE_MANAGER_SECRET: props.secret.secretName,
      },
      memorySize: 128,
      timeout: Duration.seconds(28),
      architecture: Architecture.ARM_64,
      role: this.role,
      vpc: this.vpc,
      vpcSubnets: { subnetType: SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [this.securityGroup],
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
