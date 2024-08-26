import { Construct } from 'constructs';
import * as fn from './function';
import { DatabaseProps } from './function';
import { Duration } from 'aws-cdk-lib';

/**
 * Props for the migrate function.
 */
export type MigrateFunctionProps = fn.FunctionPropsConfigurable & DatabaseProps;

/**
 * A construct for the Lambda migrate function.
 */
export class MigrateFunction extends fn.Function {
  constructor(scope: Construct, id: string, props: MigrateFunctionProps) {
    super(scope, id, {
      package: 'filemanager-migrate-lambda',
      timeout: Duration.minutes(2),
      ...props,
    });
  }
}
