import { Construct } from 'constructs';
import { Rule } from 'aws-cdk-lib/aws-events';
import { Queue } from 'aws-cdk-lib/aws-sqs';
import { SqsQueue } from 'aws-cdk-lib/aws-events-targets';
import { Alarm, ComparisonOperator, MathExpression } from 'aws-cdk-lib/aws-cloudwatch';

/**
 * Props for the `EventSource` construct.
 */
export type EventSourceProps = {
  /**
   * Buckets to receive events from.
   */
  buckets: string[];
  /**
   * The types of events to capture. If not specified, captures all events. This should be from the list
   * S3 EventBridge events: https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventBridge.html
   */
  eventTypes?: string[];
  /**
   * A prefix of the objects that are matched when receiving events from the buckets.
   */
  prefix?: string;
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

    const rule = new Rule(scope, 'Rule', {
      eventPattern: {
        source: ['aws.s3'],
        detailType: props.eventTypes,
        detail: {
          bucket: {
            name: props.buckets,
          },
          ...(props.prefix && {
            object: {
              key: [
                {
                  prefix: props.prefix,
                },
              ],
            },
          }),
        },
      },
    });

    this.queue = new Queue(this, 'Queue');
    this.deadLetterQueue = new Queue(this, 'DeadLetterQueue');
    rule.addTarget(
      new SqsQueue(this.queue, {
        deadLetterQueue: this.deadLetterQueue,
      })
    );

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
}
