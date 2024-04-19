import { Construct } from 'constructs';
import { EventSourceProps, IngestFunction } from '../constructs/functions/ingest';
import { MigrateFunction } from '../constructs/functions/migrate';
import * as fn from '../constructs/functions/function';
import { DatabaseProps } from '../constructs/functions/function';
import { Vpc, SecurityGroup, VpcLookupOptions } from 'aws-cdk-lib/aws-ec2';
import { Arn, Stack, StackProps } from 'aws-cdk-lib';
import { StringParameter } from 'aws-cdk-lib/aws-ssm';
import { ProviderFunction } from '../../../../../components/provider_function';
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
 * JWT authorization settings.
 */
export type FilemanagerJwtAuthSettings = {
  /**
   * The JWT audience.
   */
  jwtAudience?: string[];

  /**
   * The cognito user pool id for the authorizer. If this is not set, then a new user pool is created.
   */
  cogUserPoolId?: string;
};

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

    let objectsQuery = new ObjectsQueryFunction(this, 'ObjectsQueryFunction', {
      vpc: props.vpc,
      databaseSecret: props.databaseSecret,
      databaseSecurityGroup: props.databaseSecurityGroup,
      buildEnvironment: props?.buildEnvironment,
      rustLog: props?.rustLog, 
    });

    // Add an authorizer if auth is required.
    let authorizer = undefined;
    if (!settings.jwtAuthorizer.public) {
      // If the cog user pool id is not specified, create a new one.
      if (settings.jwtAuthorizer.cogUserPoolId === undefined) {
        const pool = new UserPool(this, "userPool", {
          userPoolName: "HtsgetRsUserPool",
        });
        settings.jwtAuthorizer.cogUserPoolId = pool.userPoolId;
      }

      authorizer = new HttpJwtAuthorizer(
        id + "HtsgetAuthorizer",
        `https://cognito-idp.${this.region}.amazonaws.com/${settings.jwtAuthorizer.cogUserPoolId}`,
        {
          identitySource: ["$request.header.Authorization"],
          jwtAudience: settings.jwtAuthorizer.jwtAudience ?? [],
        },
      );
    }    
    // API Gateway v2 endpoints for querying data
    const api = new HttpApi(this, 'FileManagerAPI');

    const ObjectsQueryFunctionIntegration = new HttpLambdaIntegration(
      id + "FilemanagerIntegration",
      objectsQuery.function
    );

    // Add a route to the API
    api.addRoutes({
      path: '/objects/{:id}',
      methods: [HttpMethod.GET],
      integration: ObjectsQueryFunctionIntegration,
    });
  }
}
