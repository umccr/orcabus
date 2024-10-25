import { Construct } from 'constructs';
import * as fn from './function';
import { DatabaseProps } from './function';
import { Duration, Stack } from 'aws-cdk-lib';
import { PolicyStatement } from 'aws-cdk-lib/aws-iam';

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
      // This needs to be higher to account for longer migrations.
      timeout: Duration.minutes(15),
      ...props,
    });

    // Need to be able to determine if the stack is in rollback state.
    this.addToPolicy(
      new PolicyStatement({
        actions: ['cloudformation:DescribeStacks'],
        resources: [Stack.of(this).stackId],
      })
    );
  }
}
