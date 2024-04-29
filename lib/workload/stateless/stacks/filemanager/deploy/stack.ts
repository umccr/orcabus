import { Construct } from 'constructs';
import { IngestFunction } from './constructs/functions/ingest';
import { MigrateFunction } from './constructs/functions/migrate';
import { QueryFunction } from './constructs/functions/query';
import { DatabaseProps } from './constructs/functions/function';
import { Vpc, SecurityGroup, VpcLookupOptions, IVpc, ISecurityGroup } from 'aws-cdk-lib/aws-ec2';
import { Arn, Stack, StackProps } from 'aws-cdk-lib';
import { StringParameter } from 'aws-cdk-lib/aws-ssm';
import { ProviderFunction } from '../../../../components/provider-function';
import { ApiGatewayConstruct } from '../../../../components/api-gateway';
import { IQueue, Queue } from 'aws-cdk-lib/aws-sqs';
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
  private readonly vpc: IVpc;
  private readonly host: string;
  private readonly securityGroup: ISecurityGroup;
  private readonly queue: IQueue;
  
  constructor(scope: Construct, id: string, props: FilemanagerProps) {
    super(scope, id, props);

    this.vpc = Vpc.fromLookup(this, 'MainVpc', props.vpcProps);

    this.securityGroup = SecurityGroup.fromLookupByName(
      this,
      'OrcaBusLambdaSecurityGroup',
      props.securityGroupName,
      this.vpc
    );

    this.host = StringParameter.valueForStringParameter(
      this,
      props.databaseClusterEndpointHostParameter
    );

    if (props?.migrateDatabase) {
      const migrateFunction = new MigrateFunction(this, 'MigrateFunction', {
        vpc: this.vpc,
        host: this.host,
        port: props.port,
        securityGroup: this.securityGroup,
      });

      new ProviderFunction(this, 'MigrateProviderFunction', {
        vpc: this.vpc,
        function: migrateFunction.function,
      });
    }

    this.queue = Queue.fromQueueArn(
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
    return new IngestFunction(this, 'IngestFunction', {
      vpc: this.vpc,
      host: this.host,
      securityGroup: this.securityGroup,
      eventSources: [this.queue],
      buckets: props.eventSourceBuckets,
      ...props
    });
  }

  // Query function and API Gateway fronting the function
  private createQueryFunction(props: FilemanagerProps) {
    let objectsQueryLambda = new QueryFunction(this, 'ObjectsQueryFunction', {
      vpc: this.vpc,
      host: this.host,
      securityGroup: this.securityGroup,
      ...props
    });

    const ApiGateway = new ApiGatewayConstruct(this, 'ApiGateway', {
      region: this.region,
      apiName: props.stackName,
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
