import { Construct } from 'constructs';
import { IQueue } from 'aws-cdk-lib/aws-sqs';
import * as lambdaEventSources from 'aws-cdk-lib/aws-lambda-event-sources';
import * as fn from './function';

/**
 * Settable values for the ingest function.
 */
export type IngestFunctionSettings = fn.FunctionSettings;

/**
 * Props for the ingest function.
 */
export type IngestFunctionProps = IngestFunctionSettings &
  fn.FunctionPropsNoPackage & {
    /**
     * The SQS queue URL to receive events from.
     */
    readonly queue: IQueue;
  };

/**
 * A construct for the Lambda ingest function.
 */
export class IngestFunction extends fn.Function {
  constructor(scope: Construct, id: string, props: IngestFunctionProps) {
    super(scope, id, { package: 'filemanager-ingest-lambda', ...props });

    this.addManagedPolicy('service-role/AWSLambdaSQSQueueExecutionRole');

    const eventSource = new lambdaEventSources.SqsEventSource(props.queue);
    this.function.addEventSource(eventSource);
  }
}
