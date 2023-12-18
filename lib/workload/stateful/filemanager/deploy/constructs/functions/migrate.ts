import { Construct } from 'constructs';
import { IQueue } from 'aws-cdk-lib/aws-sqs';
import * as fn from './function';

/**
 * Settable values for the migrate function.
 */
export type IngestFunctionSettings = fn.FunctionSettings;

/**
 * Props for the migrate function.
 */
export type IngestFunctionProps = IngestFunctionSettings &
  fn.FunctionPropsNoPackage & {
    /**
     * The SQS queue URL to receive events from.
     */
    readonly queue: IQueue;
  };

/**
 * A construct for the Lambda migrate function.
 */
export class MigrateFunction extends fn.Function {
  constructor(scope: Construct, id: string, props: IngestFunctionProps) {
    super(scope, id, { package: 'filemanager-migrate-lambda', ...props });
  }
}
