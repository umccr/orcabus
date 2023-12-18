import { Construct } from 'constructs';
import { RustFunction } from 'rust.aws-cdk-lambda';
import { IQueue } from 'aws-cdk-lib/aws-sqs';
import * as lambdaEventSources from 'aws-cdk-lib/aws-lambda-event-sources';
import * as fn from './function';

/**
 * Settable values for the ingest function.
 */
export type IngestFunctionSettings = {
  /**
   * Additional build environment variables when building the Lambda function.
   */
  readonly buildEnvironment?: { [key: string]: string | undefined };
  /**
   * RUST_LOG string, defaults to trace on local crates and info everywhere else.
   */
  readonly rustLog?: string;
};

/**
 * Props for the database
 */
export type IngestFunctionProps = fn.FunctionSettings &
  fn.FunctionProps & {
    /**
     * The SQS queue URL to receive events from.
     */
    readonly queue: IQueue;
  };

/**
 * A construct for the Lambda ingest function.
 */
export class IngestFunction extends Construct {
  private readonly _function: fn.Function;

  constructor(scope: Construct, id: string, props: IngestFunctionProps) {
    super(scope, id);

    this._function = new fn.Function(this, 'IngestLambdaFunction', {
      package: 'filemanager-ingest-lambda',
      buildEnvironment: props.buildEnvironment,
      rustLog: props.rustLog,
      vpc: props.vpc,
      database: props.database,
      onFailure: props.onFailure,
      policies: props.policies,
    });

    this._function.addManagedPolicy('service-role/AWSLambdaSQSQueueExecutionRole');

    const eventSource = new lambdaEventSources.SqsEventSource(props.queue);
    this.function.addEventSource(eventSource);
  }

  /**
   * Get the underlying Lambda function.
   */
  get function(): RustFunction {
    return this._function.function;
  }
}
