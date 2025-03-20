import { Construct } from 'constructs';
import { IQueue } from 'aws-cdk-lib/aws-sqs';
import * as fn from './function';
import { SqsEventSource } from 'aws-cdk-lib/aws-lambda-event-sources';
import { DatabaseProps } from './function';
import { FILEMANAGER_SERVICE_NAME } from '../../stack';

/**
 * Props for controlling access to buckets.
 */
export type BucketProps = {
  /**
   * The buckets that the filemanager is expected to process. This will add policies to access the buckets via
   * 's3:List*' and 's3:Get*'.
   */
  readonly buckets: string[];
};

/**
 * Props related to the filemanager event source.
 */
export type EventSourceProps = {
  /**
   * The SQS queue URL to receive events from.
   */
  readonly eventSources: IQueue[];
} & BucketProps;

/**
 * Props for the ingest function.
 */
export type IngestFunctionProps = fn.FunctionPropsConfigurable & DatabaseProps & EventSourceProps;

/**
 * A construct for the Lambda ingest function.
 */
export class IngestFunction extends fn.Function {
  constructor(scope: Construct, id: string, props: IngestFunctionProps) {
    super(scope, id, {
      package: 'filemanager-ingest-lambda',
      environment: {
        FILEMANAGER_INGESTER_TAG_NAME: 'umccr-org:OrcaBusFileManagerIngestId',
        FILEMANAGER_IGNORE_DIRECTORY_OBJECTS: 'true',
        ...props.environment,
      },
      ...props,
    });

    this.addAwsManagedPolicy('service-role/AWSLambdaSQSQueueExecutionRole');

    props.eventSources.forEach((source) => {
      const eventSource = new SqsEventSource(source);
      this.function.addEventSource(eventSource);
    });
    this.addPoliciesForBuckets(props.buckets, [
      ...fn.Function.getObjectActions(),
      ...fn.Function.getObjectVersionActions(),
      ...fn.Function.objectTaggingActions(),
    ]);
  }
}
