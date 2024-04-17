import { Construct } from 'constructs';
import * as fn from './function';
import { DatabaseProps } from './function';

/**
 * Props for the migrate function.
 */
export type MigrateFunctionProps = fn.FunctionPropsNoPackage & DatabaseProps;

/**
 * A construct for the Lambda migrate function.
 */
export class MigrateFunction extends fn.Function {
  constructor(scope: Construct, id: string, props: MigrateFunctionProps) {
    super(scope, id, { package: 'filemanager-migrate-lambda', ...props });
  }
}
