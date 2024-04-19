import { Construct } from 'constructs';
import { IngestFunction } from '../constructs/functions/ingest';
import { MigrateFunction } from '../constructs/functions/migrate';
import { ObjectsQueryFunction } from '../constructs/functions/query';
import { DatabaseProps } from '../constructs/functions/function';
import { Vpc, SecurityGroup, VpcLookupOptions } from 'aws-cdk-lib/aws-ec2';
import { Arn, Stack, StackProps } from 'aws-cdk-lib';
import { StringParameter } from 'aws-cdk-lib/aws-ssm';
import { ProviderFunction } from '../../../../../components/provider_function';
import { Queue } from 'aws-cdk-lib/aws-sqs';
import { HttpApi, HttpMethod } from 'aws-cdk-lib/aws-apigatewayv2';
import { HttpJwtAuthorizer } from 'aws-cdk-lib/aws-apigatewayv2-authorizers';
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import { UserPool } from 'aws-cdk-lib/aws-cognito';

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

    let objectsQueryLambda = new ObjectsQueryFunction(this, 'ObjectsQueryFunction', {
      vpc: vpc,
      host: host,
      port: props.port,
      securityGroup: lambdaSecurityGroup
    });

    const ObjectsQueryFunctionIntegration = new HttpLambdaIntegration(
      "FilemanagerQueryApiIntegration",
      objectsQueryLambda.function
    );

    const pool = new UserPool(this, "userPool", {
      userPoolName: "OrcaBusUserPool",
    });

    // JWT authorizer
    const authorizer = new HttpJwtAuthorizer(
        id + "FilemanagerQueryApiAuthorizer",
        `https://cognito-idp.${this.region}.amazonaws.com/`,
        {
          identitySource: ["meow"], //["$request.header.Authorization"],
          jwtAudience: ["aud"], // FIXME!!!
        },
      );

    // API Gateway v2 endpoints for querying data
    const api = new HttpApi(this, 'FileManagerQueryApi', {
      defaultAuthorizer: authorizer,
      defaultIntegration: ObjectsQueryFunctionIntegration,
    });

    // Add a route to the API
    api.addRoutes({
      path: '/objects/{:id}',
      methods: [HttpMethod.GET],
      integration: ObjectsQueryFunctionIntegration,
    });
  }
}
