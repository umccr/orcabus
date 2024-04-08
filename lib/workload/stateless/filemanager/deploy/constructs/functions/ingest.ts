import { Construct } from 'constructs';
import { IQueue } from 'aws-cdk-lib/aws-sqs';
import * as fn from './function';
import { PolicyStatement } from 'aws-cdk-lib/aws-iam';
import { SqsEventSource } from 'aws-cdk-lib/aws-lambda-event-sources';

/**
 * Props for the ingest function.
 */
export type IngestFunctionProps = fn.FunctionPropsNoPackage & {
    /**
     * The SQS queue URL to receive events from.
     */
    readonly eventSources: IQueue[];
    /**
     * The buckets that the filemanager is expected to process. This will add policies to access the buckets via
     * 's3:List*' and 's3:Get*'.
     */
    readonly buckets: string[];
  };

/**
 * A construct for the Lambda ingest function.
 */
export class IngestFunction extends fn.Function {
  constructor(scope: Construct, id: string, props: IngestFunctionProps) {
    super(scope, id, { package: 'filemanager-ingest-lambda', ...props });

    this.addAwsManagedPolicy('service-role/AWSLambdaSQSQueueExecutionRole');

    props.eventSources.forEach((source) => {
      const eventSource = new SqsEventSource(source);
      this.function.addEventSource(eventSource);
    });
    props.buckets.map((bucket) => {
      this.addToPolicy(new PolicyStatement({
        actions: ['s3:ListBucket', 's3:GetObject'],
        resources: [`arn:aws:s3:::${bucket}`, `arn:aws:s3:::${bucket}/*`],
      }));
    })
  }
}
