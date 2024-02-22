import { Construct } from 'constructs';
import * as fn from './function';

/**
 * Props for the (objects) query function.
 */
export type ObjectsQueryFunctionProps = fn.FunctionPropsNoPackage;

/**
 * A construct for the Lambda query function.
 */
export class ObjectsQueryFunction extends fn.Function {
  constructor(scope: Construct, id: string, props: ObjectsQueryFunctionProps) {
    super(scope, id, { package: 'filemanager-objects-query-lambda', ...props });
  }
}
