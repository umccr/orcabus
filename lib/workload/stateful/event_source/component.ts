import { Construct } from 'constructs';
import { Rule } from 'aws-cdk-lib/aws-events';
import { Queue } from 'aws-cdk-lib/aws-sqs';
import { SqsQueue } from 'aws-cdk-lib/aws-events-targets';

/**
 * Props for the `EventSource` construct.
 */
export type EventSourceProps = {
  /**
   * Bucket to receive events from.
   */
  buckets: string[];
  /**
   * The types of events to capture. If not specified, captures all events. This should be from the list
   * S3 EventBridge events: https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventBridge.html
   */
  eventTypes?: string[];
};

/**
 * A construct that defines an SQS S3 event source, along with a DLQ and CloudWatch alarms.
 */
export class EventSource extends Construct {
  readonly queue: Queue;
  readonly deadLetterQueue: Queue;

  constructor(scope: Construct, id: string, props: EventSourceProps) {
    super(scope, id);

    const rule = new Rule(scope, 'Rule', {
      eventPattern: {
        source: ['aws.s3'],
        detailType: props.eventTypes,
        detail: {
          bucket: {
            name: props.buckets
          },
        }
      }
    });

    this.queue = new Queue(this, 'Queue');
    this.deadLetterQueue = new Queue(this, 'DeadLetterQueue');
    rule.addTarget(
      new SqsQueue(this.queue, {
        deadLetterQueue: this.deadLetterQueue,
      })
    );

    this.deadLetterQueue.metricNumberOfMessagesSent().createAlarm(
      this,
      'Alarm',
      {
        threshold: 1,
        evaluationPeriods: 1
      }
    );
  }
}
