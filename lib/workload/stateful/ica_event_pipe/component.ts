import { Construct } from 'constructs';
import { Duration } from 'aws-cdk-lib';
import { IEventBus, EventBus } from 'aws-cdk-lib/aws-events';
import { MonitoredQueue } from 'sqs-dlq-monitoring';
import { Topic } from 'aws-cdk-lib/aws-sns';
import { IQueue } from 'aws-cdk-lib/aws-sqs';
import { SqsSource } from '@aws-cdk/aws-pipes-sources-alpha';
import * as pipes from '@aws-cdk/aws-pipes-alpha';
import * as iam from 'aws-cdk-lib/aws-iam';

export interface IcaEventPipeProps {
  icaEventPipeName: string;
  icaQueueName: string;
  icaQueueVizTimeout: number;
  eventBusName: string;
  slackTopicArn: string;
  dlqMessageThreshold: number;
}

export class IcaEventPipeConstruct extends Construct {
  readonly icaQueue: IQueue;
  readonly mainBus: IEventBus;

  constructor(scope: Construct, id: string, props: IcaEventPipeProps) {
    super(scope, id);
    this.icaQueue = this.createMonitoredQueue(id, props).queue;
    this.mainBus = EventBus.fromEventBusName(this, id + 'EventBus', props.eventBusName);
    this.createPipe();
  }

  // Create the INPUT SQS queue that will receive the ICA events
  // This should have a DLQ and be monitored via CloudWatch alarm and Slack notifications
  private createMonitoredQueue(id: string, props: IcaEventPipeProps) {
    const topic: Topic = Topic.fromTopicArn(this, id + 'slackTopic', props.slackTopicArn) as Topic;

    const mq = new MonitoredQueue(this, props.icaEventPipeName, {
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

    return mq;
  }

  // Create the Pipe passing the ICA event from the SQS queue to our OrcaBus event bus
  private createPipe() {
    const targetInputTransformation = pipes.InputTransformation.fromObject({
      'ica-event': pipes.DynamicInput.fromEventPath('$.body'),
    });
    return new pipes.Pipe(this, 'Pipe', {
      source: new SqsSource(this.icaQueue),
      // target: new EventBusTarget(this.mainBus),
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
