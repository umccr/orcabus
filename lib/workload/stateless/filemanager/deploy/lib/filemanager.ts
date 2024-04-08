import { Construct } from 'constructs';
import { IngestFunction, IngestFunctionProps } from '../constructs/functions/ingest';
import { MigrateFunction } from '../constructs/functions/migrate';
import * as fn from '../constructs/functions/function';
import { DatabaseProps } from '../constructs/functions/function';
import { IVpc } from 'aws-cdk-lib/aws-ec2';
import { IQueue } from 'aws-cdk-lib/aws-sqs';
import { Stack, StackProps } from 'aws-cdk-lib';
import { CdkResourceInvoke } from '../../../../components/cdk_resource_invoke';

export const FILEMANAGER_SERVICE_NAME = 'filemanager';

/**
 * Stateful config for filemanager.
 */
export type FilemanagerConfig = Omit<DatabaseProps, 'host' | 'securityGroup'> & {
  /**
   * Queue name used by the EventSource construct.
   */
  eventSourceQueueName: string;
  /**
   * Buckets defined by the EventSource construct.
   */
  eventSourceBuckets: string[];
  /**
   * The parameter name that contains the database cluster endpoint.
   */
  databaseClusterEndpointHostParameter: string;
}

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
          host: props.host,
          port: props.port,
          securityGroup: props.securityGroup,
          buildEnvironment: props?.buildEnvironment,
          rustLog: props?.rustLog,
        },
        id: 'MigrateFunction',
        // Assuming no dependencies because the database will already exist.
      });
    }

    new IngestFunction(this, 'IngestLambda', {
      vpc: props.vpc,
      host: props.host,
      port: props.port,
      securityGroup: props.securityGroup,
      eventSources: props.eventSources,
      buckets: props.buckets,
      buildEnvironment: props?.buildEnvironment,
      rustLog: props?.rustLog,
    });
  }
}
