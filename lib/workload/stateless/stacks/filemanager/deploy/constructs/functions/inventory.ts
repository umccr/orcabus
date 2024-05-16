import { Construct } from 'constructs';
import * as fn from './function';
import { DatabaseProps } from './function';

/**
 * The name of the inventory Lambda function.
 */
export const INVENTORY_FUNCTION_NAME = 'orcabus-filemanager-ingest-inventory';

export type InventoryFunctionConfig = {
  /**
   * The buckets that the inventory function can fetch data from. This function needs access to the buckets that
   * contain the `manifest.json` and data files. This option will add policies to access the buckets via
   * 's3:List*' and 's3:Get*'.
   */
  readonly buckets: string[];
}

/**
 * Props for the inventory function.
 */
export type InventoryFunctionProps = fn.FunctionPropsNoPackage & DatabaseProps & InventoryFunctionConfig;

/**
 * A construct for the Lambda inventory function.
 */
export class InventoryFunction extends fn.Function {
  constructor(scope: Construct, id: string, props: InventoryFunctionProps) {
    super(scope, id, { package: 'filemanager-inventory-lambda', ...props, functionName: INVENTORY_FUNCTION_NAME });

    this.addPoliciesForBuckets(props.buckets);
  }
}
