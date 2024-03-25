import { Construct } from 'constructs';
import { Duration } from 'aws-cdk-lib';
import { IEventBus, EventBus } from 'aws-cdk-lib/aws-events';
import { IMessagingProvider, MonitoredQueue } from 'sqs-dlq-monitoring';
import { Topic } from 'aws-cdk-lib/aws-sns';
import { IQueue, Queue, DeadLetterQueue } from 'aws-cdk-lib/aws-sqs';
import { SqsSource } from '@aws-cdk/aws-pipes-sources-alpha';
import * as pipes from '@aws-cdk/aws-pipes-alpha';
import * as chatbot from 'aws-cdk-lib/aws-chatbot';
import * as iam from 'aws-cdk-lib/aws-iam';
import { StringParameter } from 'aws-cdk-lib/aws-ssm';

export interface IcaEventPipeProps {
  icaEventPipeName: string;
  icaQueueName: string;
  icaQueueVizTimeout: number;
  slackChannelConfigurationName: string;
  slackWorkspaceIdSSMParam: string;
  slackChannelIdSSMParam: string;
  eventBusName: string;
}

export class IcaEventPipeConstruct extends Construct {
  readonly icaQueue: IQueue;
  readonly mainBus: IEventBus;

  constructor(scope: Construct, id: string, props: IcaEventPipeProps) {
    super(scope, id);
    this.icaQueue = this.createMonitoredQueue(id, props).queue;
    this.mainBus = EventBus.fromEventBusName(this, id + 'EventBus', props.eventBusName);
  }

  private createMonitoredQueue(id: string, props: IcaEventPipeProps) {
    const slackWorkspaceId = StringParameter.fromStringParameterName(this, id + 'SlackWorkspaceId', props.slackWorkspaceIdSSMParam).stringValue;
    const slackChannelId = StringParameter.fromStringParameterName(this, id + 'slackChannelId', props.slackChannelIdSSMParam).stringValue;

    const queue = new Queue(this, id + 'DLQ', {
      queueName: props.icaQueueName + '-dlq',
      enforceSSL: true,
      visibilityTimeout: Duration.seconds(props.icaQueueVizTimeout),
    });

    const deadLetterQueue: DeadLetterQueue = {
      queue: queue,
      maxReceiveCount: 3,
    };

    const mq = new MonitoredQueue(this, props.icaEventPipeName, {
      queueProps: {
        queueName: props.icaQueueName,
        deadLetterQueue: deadLetterQueue,
        enforceSSL: true,
        visibilityTimeout: Duration.seconds(props.icaQueueVizTimeout),
      },
      messagingProviders: [
        new ChatbotMessageProvider(
          props.slackChannelConfigurationName,
          slackWorkspaceId,
          slackChannelId,
        ),
      ],
    });

    return mq;
  }

  private createPipe() {
    // const inputTransfrom = new pipes.InputTransformation()
    return new pipes.Pipe(this, 'Pipe', {
      source: new SqsSource(this.icaQueue),
      target: new EventBusTarget(this.mainBus),
      // target: new EventBusTarget(this.mainBus, {inputTransformation: inputTransfrom}), // TODO implement
    });
  }
}

class EventBusTarget implements pipes.ITarget {
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

class ChatbotMessageProvider implements IMessagingProvider {
  readonly slackChannelConfigurationName: string;
  readonly slackWorkspaceId: string;
  readonly slackChannelId: string;

  constructor(
    slackChannelConfigurationName: string,
    slackWorkspaceId: string,
    slackChannelId: string
  ) {
    this.slackChannelConfigurationName = slackChannelConfigurationName;
    this.slackWorkspaceId = slackWorkspaceId;
    this.slackChannelId = slackChannelId;
  }

  deployProvider(scope: Construct, topic: Topic) {
    new chatbot.SlackChannelConfiguration(scope, 'id', {
      slackChannelConfigurationName: this.slackChannelConfigurationName,
      slackWorkspaceId: this.slackWorkspaceId,
      slackChannelId: this.slackChannelId,
      notificationTopics: [topic],
    });
  }
}


