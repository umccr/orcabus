import { Construct } from 'constructs';
import { EventSourceProps, IngestFunction, IngestFunctionProps } from '../constructs/functions/ingest';
import { MigrateFunction } from '../constructs/functions/migrate';
import * as fn from '../constructs/functions/function';
import { DatabaseProps } from '../constructs/functions/function';
import { IVpc } from 'aws-cdk-lib/aws-ec2';
import { IQueue } from 'aws-cdk-lib/aws-sqs';
import { Stack, StackProps } from 'aws-cdk-lib';
import { CdkResourceInvoke } from '../../../../components/cdk_resource_invoke';
import { StringParameter } from 'aws-cdk-lib/aws-ssm';

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
export type FilemanagerProps = StackProps & EventSourceProps & fn.FunctionPropsNoPackage & Omit<DatabaseProps, 'host'> & {
    /**
     * VPC to use for filemanager.
     */
    readonly vpc: IVpc,
    /**
     * Whether to initialize a database migration.
     */
    readonly migrateDatabase?: boolean;
    /**
     * The parameter name that contains the database cluster endpoint.
     */
    readonly databaseClusterEndpointHostParameter: string;
};

/**
 * Construct used to configure the filemanager.
 */
export class Filemanager extends Stack {
  constructor(scope: Construct, id: string, props: FilemanagerProps) {
    super(scope, id, props);

    const host = StringParameter.valueForStringParameter(
      this,
      props.databaseClusterEndpointHostParameter
    );

    if (props?.migrateDatabase) {
      new CdkResourceInvoke(this, 'MigrateDatabase', {
        vpc: props.vpc,
        createFunction: (scope: Construct, id: string, props: fn.FunctionPropsNoPackage & DatabaseProps) => {
          return new MigrateFunction(scope, id, props);
        },
        functionProps: {
          vpc: props.vpc,
          host: host,
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
      host: host,
      port: props.port,
      securityGroup: props.securityGroup,
      eventSources: props.eventSources,
      buckets: props.buckets,
      buildEnvironment: props?.buildEnvironment,
      rustLog: props?.rustLog,
    });
  }
}
