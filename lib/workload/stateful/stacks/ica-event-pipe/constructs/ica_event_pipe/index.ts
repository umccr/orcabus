import { Construct } from 'constructs';
import { Duration } from 'aws-cdk-lib';
import { IEventBus, EventBus } from 'aws-cdk-lib/aws-events';
import { MonitoredQueue } from 'sqs-dlq-monitoring';
import { Topic } from 'aws-cdk-lib/aws-sns';
import { IQueue } from 'aws-cdk-lib/aws-sqs';
import { SqsSource } from '@aws-cdk/aws-pipes-sources-alpha';
import * as pipes from '@aws-cdk/aws-pipes-alpha';
import * as iam from 'aws-cdk-lib/aws-iam';

/**
 * Definition of the IcaEventPipe properties.
 */
export interface IcaEventPipeConstructProps {
  /** The name for the Event Pipe */
  icaEventPipeName: string;
  /** The name for the incoming SQS queue (the DLQ with use this name with a "-dlq" postfix) */
  icaQueueName: string;
  /** The visibility timeout for the queue */
  icaQueueVizTimeout: number;
  /** The name of the Event Bus to forward events to (used to lookup the Event Bus) */
  eventBusName: string;
  /** The ARN of the SNS Topic to receive DLQ notifications from CloudWatch */
  slackTopicArn: string;
  /** The CloudWatch Alarm threshold to use before raising an alarm */
  dlqMessageThreshold: number;
  /** The ICA account to grant publish permissions to */
  icaAwsAccountNumber: string;
}

export class IcaEventPipeConstruct extends Construct {
  readonly icaQueue: IQueue;
  readonly mainBus: IEventBus;

  constructor(scope: Construct, id: string, props: IcaEventPipeConstructProps) {
    super(scope, id);
    this.icaQueue = this.createMonitoredQueue(id, props).queue;
    this.mainBus = EventBus.fromEventBusName(this, 'EventBus', props.eventBusName);
    this.createPipe(props.icaEventPipeName);
  }

  // Create the INPUT SQS queue that will receive the ICA events
  // This should have a DLQ and be monitored via CloudWatch alarm and Slack notifications
  private createMonitoredQueue(id: string, props: IcaEventPipeConstructProps) {
    // Note: the construct MonitoredQueue demands a "Topic" construct as it usually modifies the topic adding subscriptions.
    // However, our use case, as we don't add any additional subscriptions, does not require topic modification, so we can pass on an "ITopic" as "Topic".
    const topic: Topic = Topic.fromTopicArn(this, 'SlackTopic', props.slackTopicArn) as Topic;

    const mq = new MonitoredQueue(this, props.icaQueueName, {
      queueProps: {
        queueName: props.icaQueueName,
        enforceSSL: true,
        visibilityTimeout: Duration.seconds(props.icaQueueVizTimeout),
      },
      dlqProps: {
        queueName: props.icaQueueName + '-dlq',
        enforceSSL: true,
        visibilityTimeout: Duration.seconds(props.icaQueueVizTimeout),
      },
      messageThreshold: props.dlqMessageThreshold,
      topic: topic,
    });
    mq.queue.grantSendMessages(new iam.AccountPrincipal(props.icaAwsAccountNumber));

    return mq;
  }

  // Create the Pipe passing the ICA event from the SQS queue to our OrcaBus event bus
  private createPipe(pipeName: string) {
    const targetInputTransformation = pipes.InputTransformation.fromObject({
      'ica-event': pipes.DynamicInput.fromEventPath('$.body'),
    });
    return new pipes.Pipe(this, 'Pipe', {
      pipeName: pipeName,
      source: new SqsSource(this.icaQueue),
      target: new EventBusTarget(this.mainBus, { inputTransformation: targetInputTransformation }),
    });
  }
}

// Creates a pipe TARGET wrapping an EventBus
class EventBusTarget implements pipes.ITarget {
  // No official EventBusTarget implementations exist (yet). This is following recommendations from:
  // https://constructs.dev/packages/@aws-cdk/aws-pipes-alpha/v/2.133.0-alpha.0?lang=typescript#example-target-implementation
  targetArn: string;
  private inputTransformation: pipes.IInputTransformation | undefined;

  constructor(
    private readonly eventBus: IEventBus,
    props: { inputTransformation?: pipes.IInputTransformation } = {}
  ) {
    this.eventBus = eventBus;
    this.targetArn = eventBus.eventBusArn;
    this.inputTransformation = props?.inputTransformation;
  }

  bind(_pipe: pipes.Pipe): pipes.TargetConfig {
    return {
      targetParameters: {
        inputTemplate: this.inputTransformation?.bind(_pipe).inputTemplate,
      },
    };
  }

  grantPush(pipeRole: iam.IRole): void {
    this.eventBus.grantPutEventsTo(pipeRole);
  }
}
