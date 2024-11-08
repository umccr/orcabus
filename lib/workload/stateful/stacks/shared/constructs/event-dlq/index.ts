import { Construct } from 'constructs';
import { IQueue, Queue } from 'aws-cdk-lib/aws-sqs';
import { Alarm, ComparisonOperator, MathExpression } from 'aws-cdk-lib/aws-cloudwatch';

/**
 * Properties for the EventDLQConstruct.
 */
export type EventDLQProps = {
  /**
   * The name of the dead letter queue for the construct.
   */
  queueName: string;
  /**
   * Specify the name of the alarm.
   */
  alarmName: string;
};

/**
 * A wrapper around an SQS queue that should act as a dead-letter queue.
 * Note that this is intentionally not a Construct so that the queue is flattened
 * within the parent construct.
 */
export class EventDLQConstruct {
  readonly deadLetterQueue: Queue;
  readonly alarm: Alarm;

  constructor(scope: Construct, queueId: string, alarmId: string, props: EventDLQProps) {
    this.deadLetterQueue = new Queue(scope, queueId, {
      queueName: `${props.queueName}`,
      enforceSSL: true,
    });

    const rateOfMessages = new MathExpression({
      expression: 'RATE(visible + notVisible)',
      usingMetrics: {
        visible: this.deadLetterQueue.metricApproximateNumberOfMessagesVisible(),
        notVisible: this.deadLetterQueue.metricApproximateNumberOfMessagesVisible(),
      },
    });

    this.alarm = new Alarm(scope, alarmId, {
      metric: rateOfMessages,
      comparisonOperator: ComparisonOperator.GREATER_THAN_THRESHOLD,
      threshold: 0,
      evaluationPeriods: 1,
      alarmName: props.alarmName,
      alarmDescription: 'An event has been received in the dead letter queue.',
    });
  }

  /**
   * Get the SQS queue ARN.
   */
  get queueArn(): string {
    return this.queue.queueArn;
  }

  /**
   * Get the dead letter queue.
   */
  get queue(): IQueue {
    return this.deadLetterQueue;
  }
}
