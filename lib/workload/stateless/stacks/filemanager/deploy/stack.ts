import { Construct } from 'constructs';
import { IngestFunction } from './constructs/functions/ingest';
import { MigrateFunction } from './constructs/functions/migrate';
import { ObjectsQueryFunction } from './constructs/functions/query';
import { DatabaseProps } from './constructs/functions/function';
import { Vpc, SecurityGroup, VpcLookupOptions } from 'aws-cdk-lib/aws-ec2';
import { Arn, Stack, StackProps } from 'aws-cdk-lib';
import { StringParameter } from 'aws-cdk-lib/aws-ssm';
import { ProviderFunction } from '../../../../components/provider_function';
import { ApiGatewayConstruct } from '../../../../components/api-gateway';
import { Queue } from 'aws-cdk-lib/aws-sqs';
import { HttpMethod, HttpRoute, HttpRouteKey } from 'aws-cdk-lib/aws-apigatewayv2';
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';

export const FILEMANAGER_SERVICE_NAME = 'filemanager';

/**
 * Stateful config for filemanager.
 */
export type FilemanagerConfig = Omit<DatabaseProps, 'host' | 'securityGroup'> & {
  eventSourceQueueName: string;
  eventSourceBuckets: string[];
  databaseClusterEndpointHostParameter: string;
  vpcProps: VpcLookupOptions;
  migrateDatabase?: boolean;
  securityGroupName: string;
  cognitoUserPoolIdParameterName: string;
  cognitoPortalAppClientIdParameterName: string;
  cognitoStatusPageAppClientIdParameterName: string;
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

    this.createIngestFunction(props);
    this.createQueryFunction(props);
  }

  /// Lambda function definitions and surrounding infra
  // Ingest function
  private createIngestFunction(props: FilemanagerProps) {
    new IngestFunction(this, 'IngestFunction', props);
  };

  // Api Gateway fronting filemanager's query lambda
  private createQueryFunction(props: FilemanagerProps) {
    let objectsQueryLambda = new ObjectsQueryFunction(this, 'ObjectsQueryFunction', props);

    const ApiGateway = new ApiGatewayConstruct(this, 'ApiGatewayConstruct-'+props.stackName, {
      region: this.region,
      ...props,
    });
    const httpApi = ApiGateway.httpApi;

    const apiIntegration = new HttpLambdaIntegration('ApiIntegration', objectsQueryLambda.function);

    new HttpRoute(this, 'HttpRoute', { // FIXME: Should not be just proxy but objects/{:id}
      httpApi: httpApi,
      integration: apiIntegration,
      routeKey: HttpRouteKey.with('/{proxy+}', HttpMethod.ANY),
    });
  }
}
