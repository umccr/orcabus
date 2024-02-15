import { Construct } from 'constructs';
import { Rule } from 'aws-cdk-lib/aws-events';
import { Queue } from 'aws-cdk-lib/aws-sqs';
import { SqsQueue } from 'aws-cdk-lib/aws-events-targets';
import { Alarm, ComparisonOperator, MathExpression } from 'aws-cdk-lib/aws-cloudwatch';
import { ServicePrincipal } from 'aws-cdk-lib/aws-iam';

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
   * A prefix of the objects that are matched when receiving events from the buckets.
   */
  prefix?: string;
};

/**
 * Properties for the EventSource construct.
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
   * A set of EventBridge rules to define..
   */
  rules: EventSourceRule[];
};

/**
 * A construct that defines an SQS S3 event source, along with a DLQ and CloudWatch alarms.
 */
export class EventSource extends Construct {
  readonly queue: Queue;
  readonly deadLetterQueue: Queue;
  readonly alarm: Alarm;

  constructor(scope: Construct, id: string, props: EventSourceProps) {
    super(scope, id);

    this.deadLetterQueue = new Queue(this, 'DeadLetterQueue');
    this.queue = new Queue(this, 'Queue', {
      queueName: props.queueName,
      deadLetterQueue: {
        maxReceiveCount: props.maxReceiveCount,
        queue: this.deadLetterQueue,
      },
    });

    for (const prop of props.rules) {
      const rule = new Rule(scope, 'Rule', {
        eventPattern: {
          source: ['aws.s3'],
          detailType: prop.eventTypes,
          detail: {
            ...(prop.bucket && {
              bucket: {
                name: prop.bucket,
              },
            }),
            ...(prop.prefix && {
              object: {
                key: [
                  {
                    prefix: prop.prefix,
                  },
                ],
              },
            }),
          },
        },
      });

      rule.addTarget(new SqsQueue(this.queue));
    }

    this.queue.grantSendMessages(new ServicePrincipal('events.amazonaws.com'));

    const rateOfMessages = new MathExpression({
      expression: 'RATE(visible + notVisible)',
      usingMetrics: {
        visible: this.deadLetterQueue.metricApproximateNumberOfMessagesVisible(),
        notVisible: this.deadLetterQueue.metricApproximateNumberOfMessagesVisible(),
      },
    });

    this.alarm = new Alarm(this, 'Alarm', {
      metric: rateOfMessages,
      comparisonOperator: ComparisonOperator.GREATER_THAN_THRESHOLD,
      threshold: 0,
      evaluationPeriods: 1,
      alarmName: 'Orcabus EventSource Alarm',
      alarmDescription: 'An event has been received in the dead letter queue.',
    });
  }

  /**
   * Get the SQS queue ARN.
   */
  get queueArn(): string {
    return this.queue.queueArn;
  }
}
