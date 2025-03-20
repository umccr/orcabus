import { Construct } from 'constructs';
import { EventPattern, Rule } from 'aws-cdk-lib/aws-events';
import { Queue } from 'aws-cdk-lib/aws-sqs';
import { SqsQueue } from 'aws-cdk-lib/aws-events-targets';
import { ServicePrincipal } from 'aws-cdk-lib/aws-iam';
import { EventDLQConstruct } from '../event-dlq';

/**
 * Properties for defining an S3 EventBridge rule.
 */
export type EventSourceRule = {
  /**
   * Bucket to receive events from. If not specified, captures events from all buckets.
   */
  bucket?: string;

  /**
   * The types of events to capture for the bucket. If not specified, captures all events.
   * This should be from the list S3 EventBridge events:
   * https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventBridge.html
   */
  eventTypes?: string[];

  /**
   * Rules matching specified fields inside "object" in the S3 event.
   */
  patterns?: { [key: string]: any };
};

/**
 * Properties for the EventSourceConstruct.
 */
export type EventSourceProps = {
  /**
   * The name of the queue to construct.
   */
  queueName: string;

  /**
   * The maximum number of times a message can be unsuccessfully received before
   * pushing it to the DLQ.
   */
  maxReceiveCount: number;

  /**
   * A set of EventBridge rules to define.
   */
  rules: EventSourceRule[];
};

/**
 * A construct that defines an SQS S3 event source, along with a DLQ and CloudWatch alarms.
 */
export class EventSourceConstruct extends Construct {
  readonly queue: Queue;
  readonly deadLetterQueue: EventDLQConstruct;
  readonly rules: Rule[] = [];

  constructor(scope: Construct, id: string, props: EventSourceProps) {
    super(scope, id);

    this.deadLetterQueue = new EventDLQConstruct(this, 'DeadLetterQueue', 'Alarm', {
      queueName: `${props.queueName}-dlq`,
      alarmName: 'Orcabus EventSource Alarm',
    });
    this.queue = new Queue(this, 'Queue', {
      queueName: props.queueName,
      enforceSSL: true,
      deadLetterQueue: {
        maxReceiveCount: props.maxReceiveCount,
        queue: this.deadLetterQueue.queue,
      },
    });

    let cnt = 1;
    for (const prop of props.rules) {
      const eventPattern = {
        source: ['aws.s3'],
        detailType: prop.eventTypes,
        detail: {
          ...(prop.bucket && {
            bucket: {
              name: [prop.bucket],
            },
          }),
          ...(prop.patterns && {
            object: prop.patterns,
          }),
        },
      };

      const rule = new Rule(scope, 'Rule' + cnt, {
        eventPattern,
      });
      this.rules.push(rule);

      rule.addTarget(new SqsQueue(this.queue));
      cnt += 1;
    }

    this.queue.grantSendMessages(new ServicePrincipal('events.amazonaws.com'));
  }

  /**
   * Get the SQS queue ARN.
   */
  get queueArn(): string {
    return this.queue.queueArn;
  }
}
