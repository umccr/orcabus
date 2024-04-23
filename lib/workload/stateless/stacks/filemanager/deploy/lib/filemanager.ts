import { Construct } from 'constructs';
import { IngestFunction } from '../constructs/functions/ingest';
import { MigrateFunction } from '../constructs/functions/migrate';
import { DatabaseProps } from '../constructs/functions/function';
import { Vpc, SecurityGroup, VpcLookupOptions } from 'aws-cdk-lib/aws-ec2';
import { Arn, Stack, StackProps } from 'aws-cdk-lib';
import { StringParameter } from 'aws-cdk-lib/aws-ssm';
import { ProviderFunction } from '../../../../../components/provider-function';
import { Queue } from 'aws-cdk-lib/aws-sqs';

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
  /**
   * The parameter name that contains the database cluster endpoint.
   */
  vpcProps: VpcLookupOptions;
  /**
   * Whether to initialize a database migration.
   */
  migrateDatabase?: boolean;
  /**
   * The security group name to be attached to lambdas. 
   */
  securityGroupName: string;
}

/**
 * Props for the filemanager stack.
 */
export type FilemanagerProps = StackProps & FilemanagerConfig;

/**
 * Construct used to configure the filemanager.
 */
export class Filemanager extends Stack {
  constructor(scope: Construct, id: string, props: FilemanagerProps) {
    super(scope, id, props);

    const vpc = Vpc.fromLookup(this, 'MainVpc', props.vpcProps);

    const lambdaSecurityGroup = SecurityGroup.fromLookupByName(
      this,
      'OrcaBusLambdaSecurityGroup',
      props.securityGroupName,
      vpc
    );

    const host = StringParameter.valueForStringParameter(
      this,
      props.databaseClusterEndpointHostParameter
    );

    if (props?.migrateDatabase) {
      const migrateFunction = new MigrateFunction(this, 'MigrateFunction', {
        vpc: vpc,
        host: host,
        port: props.port,
        securityGroup: lambdaSecurityGroup,
      });

      new ProviderFunction(this, 'MigrateProviderFunction', {
        vpc: vpc,
        function: migrateFunction.function,
      });
    }

    const queue = Queue.fromQueueArn(
      this,
      'FilemanagerQueue',
      Arn.format(
        {
          resource: props.eventSourceQueueName,
          service: 'sqs',
        },
        this
      )
    );

    new IngestFunction(this, 'IngestLambda', {
      vpc: vpc,
      host: host,
      port: props.port,
      securityGroup: lambdaSecurityGroup,
      eventSources: [queue],
      buckets: props.eventSourceBuckets,
    });
  }
}

