import { Construct } from 'constructs';
import { Stack, StackProps } from 'aws-cdk-lib';
import { IcaEventPipeConstruct, IcaEventPipeConstructProps } from './constructs/ica_event_pipe';

const alarmThreshod: number = 1;
const queueVizTimeout: number = 30;

/**
 * IcaEventPipeStackProps
 */
export interface IcaEventPipeStackProps {
  /** The name for stack */
  name: string;
  /** The name of the Event Bus to forward events to (used to lookup the Event Bus) */
  eventBusName: string;
  /** The name of the SNS Topic to receive DLQ notifications from CloudWatch */
  slackTopicName: string;
  /** The ICA account to grant publish permissions to */
  icaAwsAccountNumber: string;
}

export class IcaEventPipeStack extends Stack {
  constructor(scope: Construct, id: string, props: StackProps & IcaEventPipeStackProps) {
    super(scope, id, props);
    this.createPipeConstruct(this, 'IcaEventPipeConstruct', props);
  }

  private createPipeConstruct(
    scope: Construct,
    id: string,
    props: StackProps & IcaEventPipeStackProps
  ) {
    const constructProps: IcaEventPipeConstructProps = {
      icaEventPipeName: props.name + 'Pipe',
      icaQueueName: props.name + 'Queue',
      icaQueueVizTimeout: queueVizTimeout,
      eventBusName: props.eventBusName,
      dlqMessageThreshold: alarmThreshod,
      slackTopicArn: this.constructTopicArn(props),
      icaAwsAccountNumber: props.icaAwsAccountNumber,
    };
    return new IcaEventPipeConstruct(scope, id, constructProps);
  }

  private constructTopicArn(props: StackProps & IcaEventPipeStackProps) {
    if (!props.env) {
      throw new Error('No env properties found. Please ensure env.account and evn.region are set.');
    }
    if (!props.env.account) {
      throw new Error('No account');
    }
    if (!props.env.region) {
      throw new Error('No region');
    }
    return 'arn:aws:sns:' + props.env.region + ':' + props.env.account + ':' + props.slackTopicName;
  }
}
