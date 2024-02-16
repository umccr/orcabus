import { Construct } from 'constructs';
import { IngestFunction, IngestFunctionProps } from '../constructs/functions/ingest';
import { CdkResourceInvoke } from '../../../functions/cdk_resource_invoke';
import { MigrateFunction } from '../constructs/functions/migrate';
import * as fn from '../constructs/functions/function';
import { ISecurityGroup, IVpc } from 'aws-cdk-lib/aws-ec2';
import { IQueue } from 'aws-cdk-lib/aws-sqs';
import { ISecret } from 'aws-cdk-lib/aws-secretsmanager';

/**
 * Props for the filemanager stack.
 */
type FilemanagerProps = IngestFunctionProps & {
    /**
     * VPC to use for filemanager.
     */
    readonly vpc: IVpc,
    /**
     * The database secret.
     */
    readonly databaseSecret: ISecret;
    /**
     * The database security group.
     */
    readonly databaseSecurityGroup: ISecurityGroup;
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
export class Filemanager extends Construct {
  constructor(scope: Construct, id: string, settings: FilemanagerProps) {
    super(scope, id);

    if (settings?.migrateDatabase) {
      new CdkResourceInvoke(this, 'MigrateDatabase', {
        vpc: settings.vpc,
        createFunction: (scope: Construct, id: string, props: fn.FunctionPropsNoPackage) => {
          return new MigrateFunction(scope, id, props);
        },
        functionProps: {
          vpc: settings.vpc,
          databaseSecret: settings.databaseSecret,
          databaseSecurityGroup: settings.databaseSecurityGroup,
          buildEnvironment: settings?.buildEnvironment,
          rustLog: settings?.rustLog,
        },
        id: 'MigrateFunction',
        // Assuming no dependencies because the database will already exist.
      });
    }

    new IngestFunction(this, 'IngestLambda', {
      vpc: settings.vpc,
      databaseSecret: settings.databaseSecret,
      databaseSecurityGroup: settings.databaseSecurityGroup,
      eventSources: settings.eventSources,
      buckets: settings.buckets,
      buildEnvironment: settings?.buildEnvironment,
      rustLog: settings?.rustLog,
    });
  }
}
