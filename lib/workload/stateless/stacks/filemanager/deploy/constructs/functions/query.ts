import { Construct } from 'constructs';
import * as fn from './function';
import { DatabaseProps } from './function';

/**
 * Props for the (objects) query function.
 */
export type ObjectsQueryFunctionProps = fn.FunctionPropsNoPackage & DatabaseProps;

/**
 * A construct for the Lambda query function.
 */
export class QueryFunction extends fn.Function {
  constructor(scope: Construct, id: string, props: ObjectsQueryFunctionProps) {
    super(scope, id, { package: 'filemanager-api', ...props });
  }
}
