import { Construct } from 'constructs';
import * as fn from './function';
import { DatabaseProps } from './function';

/**
 * The name of the inventory Lambda function.
 */
export const INVENTORY_FUNCTION_NAME = 'orcabus-filemanager-inventory';

export type InventoryFunctionConfig = {
  /**
   * The buckets that the inventory function can fetch data from. This function needs access to the buckets that
   * contain the `manifest.json` and data files. This option will add policies to access the buckets via
   * 's3:List*' and 's3:Get*'.
   */
  readonly buckets: string[];
};

/**
 * Props for the inventory function.
 */
export type InventoryFunctionProps = fn.FunctionPropsConfigurable &
  DatabaseProps &
  InventoryFunctionConfig;

/**
 * A construct for the Lambda inventory function.
 */
export class InventoryFunction extends fn.Function {
  constructor(scope: Construct, id: string, props: InventoryFunctionProps) {
    super(scope, id, {
      package: 'filemanager-inventory-lambda',
      environment: {
        FILEMANAGER_INGESTER_TAG_NAME: 'umccr-org:OrcaBusFileManagerIngestId',
        FILEMANAGER_IGNORE_DIRECTORY_OBJECTS: 'true',
        ...props.environment,
      },
      ...props,
      functionName: INVENTORY_FUNCTION_NAME,
    });

    this.addPoliciesForBuckets(props.buckets, [
      ...fn.Function.getObjectActions(),
      ...fn.Function.getObjectVersionActions(),
      ...fn.Function.objectTaggingActions(),
    ]);
  }
}
