import { Construct } from 'constructs';
import { IngestFunction, IngestFunctionProps } from '../constructs/functions/ingest';
import { CdkResourceInvoke } from '../../../functions/cdk_resource_invoke';
import { MigrateFunction } from '../constructs/functions/migrate';
import * as fn from '../constructs/functions/function';
import { IVpc } from 'aws-cdk-lib/aws-ec2';
import { IQueue } from 'aws-cdk-lib/aws-sqs';
import { DatabaseProps } from '../constructs/functions/function';
import { Stack, StackProps } from 'aws-cdk-lib';

/**
 * Props for the filemanager stack.
 */
type FilemanagerProps = StackProps & IngestFunctionProps & DatabaseProps & {
    /**
     * VPC to use for filemanager.
     */
    readonly vpc: IVpc,
    /**
     * Whether to initialize a database migration.
     */
    readonly migrateDatabase?: boolean;
    /**
     * Event sources to use for the filemanager
     */
    readonly eventSources: IQueue[];
    /**
     * The buckets that the filemanager is expected to process. This will add policies to access the buckets via
     * 's3:List*' and 's3:Get*'.
     */
    readonly buckets: string[];
};

/**
 * Construct used to configure the filemanager.
 */
export class Filemanager extends Stack {
  constructor(scope: Construct, id: string, props: FilemanagerProps) {
    super(scope, id, props);

    if (props?.migrateDatabase) {
      new CdkResourceInvoke(this, 'MigrateDatabase', {
        vpc: props.vpc,
        createFunction: (scope: Construct, id: string, props: fn.FunctionPropsNoPackage) => {
          return new MigrateFunction(scope, id, props);
        },
        functionProps: {
          vpc: props.vpc,
          databaseSecret: props.databaseSecret,
          databaseSecurityGroup: props.databaseSecurityGroup,
          buildEnvironment: props?.buildEnvironment,
          rustLog: props?.rustLog,
        },
        id: 'MigrateFunction',
        // Assuming no dependencies because the database will already exist.
      });
    }

    new IngestFunction(this, 'IngestLambda', {
      vpc: props.vpc,
      databaseSecret: props.databaseSecret,
      databaseSecurityGroup: props.databaseSecurityGroup,
      eventSources: props.eventSources,
      buckets: props.buckets,
      buildEnvironment: props?.buildEnvironment,
      rustLog: props?.rustLog,
    });
  }
}
