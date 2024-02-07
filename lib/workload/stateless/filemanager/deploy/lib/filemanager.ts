import { Construct } from 'constructs';
import { IngestFunction, IngestFunctionSettings } from '../constructs/functions/ingest';
import { CdkResourceInvoke } from '../constructs/cdk_resource_invoke';
import { MigrateFunction } from '../constructs/functions/migrate';
import * as fn from '../constructs/functions/function';
import { IDatabase } from '../../../../stateful/database/component';
import { IVpc } from 'aws-cdk-lib/aws-ec2';
import { IQueue } from 'aws-cdk-lib/aws-sqs';
import { IDestination } from 'aws-cdk-lib/aws-lambda';

/**
 * Common settings for the filemanager stack.
 */
type Settings = IngestFunctionSettings & {
    /**
     * VPC to use for filemanager.
     */
    readonly vpc: IVpc,
    /**
     * The database for filemanager.
     */
    readonly database: IDatabase;
    /**
     * Whether to initialize a database migration.
     */
    readonly migrateDatabase?: boolean;
    /**
     * Event sources to use for the filemanager
     */
    readonly eventSources: IQueue[];
    /**
     * Location to send any events that could not be processed.
     */
    readonly onFailure: IDestination;
    /**
     * The buckets that the filemanager is expected to process. This will add policies to access the buckets via
     * 's3:List*' and 's3:Get*'.
     */
    readonly buckets: string[];
};

/**
 * Construct used to configure the filemanager.
 */
export class Filemanager extends Construct {
  constructor(scope: Construct, id: string, settings: Settings) {
    super(scope, id);

    if (settings?.migrateDatabase) {
      new CdkResourceInvoke(this, 'MigrateDatabase', {
        vpc: settings.vpc,
        createFunction: (scope: Construct, id: string, props: fn.FunctionPropsNoPackage) => {
          return new MigrateFunction(scope, id, props);
        },
        functionProps: {
          vpc: settings.vpc,
          database: settings.database,
          buildEnvironment: settings?.buildEnvironment,
          rustLog: settings?.rustLog,
        },
        id: 'MigrateFunction',
        dependencies: [settings.database.cluster],
      });
    }

    new IngestFunction(this, 'IngestLambda', {
      vpc: settings.vpc,
      database: settings.database,
      eventSources: settings.eventSources,
      onFailure: settings.onFailure,
      buckets: settings.buckets,
      buildEnvironment: settings?.buildEnvironment,
      rustLog: settings?.rustLog,
    });
  }
}
