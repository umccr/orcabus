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

/**
 * Config for the attribute linker.
 */
export type AttributeLinkerConfig = {
  vpcProps: VpcLookupOptions;
  eventBusName: string;
};

/**
 * Props for the attribute linker stack which can be configured
 */
export type AttributeLinkerConfigurableProps = StackProps & AttributeLinkerConfig;

/**
 * Props for the attribute linker stack.
 */
export type AttributeLinkerProps = AttributeLinkerConfigurableProps & {
  domainName: string;
};

/**
 * Construct used to configure the attribute linker.
 */
export class AttributeAnnotator extends Stack {
  private readonly vpc: IVpc;
  private readonly securityGroup: ISecurityGroup;
  private readonly eventBus: IEventBus;

  constructor(scope: Construct, id: string, props: AttributeLinkerProps) {
    super(scope, id, props);

    this.vpc = Vpc.fromLookup(this, 'MainVpc', props.vpcProps);
    this.eventBus = EventBus.fromEventBusName(this, 'OrcaBusMain', props.eventBusName);

    this.securityGroup = new SecurityGroup(this, 'SecurityGroup', {
      vpc: this.vpc,
      allowAllOutbound: true,
      description: 'Security group that allows the attribute linker Lambda to egress out.',
    });

    const entry = path.join(__dirname, '..');
    const fn = new GoFunction(this, 'handler', {
      entry,
      environment: {
        ANNOTATOR_FILEMANAGER_ENDPOINT: props.domainName,
      },
      memorySize: 128,
      timeout: Duration.seconds(28),
      architecture: Architecture.ARM_64,
      vpc: this.vpc,
      vpcSubnets: { subnetType: SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [this.securityGroup],
    });

    const eventRule = new Rule(this, 'EventRule', {
      description: 'Send WorkflowRunStateChange events to the AttributeLinker Lambda',
      eventBus: this.eventBus,
    });

    eventRule.addTarget(new targets.LambdaFunction(fn));
    eventRule.addEventPattern({
      source: ['orcabus.workflowmanager'],
      detailType: ['WorkflowRunStateChange'],
      detail: {
        status: [
          { 'equals-ignore-case': 'SUCCEEDED' },
          { 'equals-ignore-case': 'FAILED' },
          { 'equals-ignore-case': 'ABORTED' },
          { 'equals-ignore-case': 'TEST' },
        ],
      },
    });
  }
}
