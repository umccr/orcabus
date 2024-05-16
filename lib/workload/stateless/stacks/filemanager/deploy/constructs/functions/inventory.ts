import { Construct } from 'constructs';
import * as fn from './function';
import { DatabaseProps } from './function';

/**
 * Props for the inventory function.
 */
export type InventoryFunctionProps = fn.FunctionPropsNoPackage & DatabaseProps;

/**
 * A construct for the Lambda inventory function.
 */
export class InventoryFunction extends fn.Function {
  constructor(scope: Construct, id: string, props: InventoryFunctionProps) {
    super(scope, id, { package: 'filemanager-inventory-lambda', ...props });
  }
}
