import { Construct } from 'constructs';
import { IngestFunction } from './constructs/functions/ingest';
import { MigrateFunction } from './constructs/functions/migrate';
import { ApiFunction } from './constructs/functions/api';
import { DatabaseProps } from './constructs/functions/function';
import { Vpc, SecurityGroup, VpcLookupOptions, IVpc, ISecurityGroup } from 'aws-cdk-lib/aws-ec2';
import { Arn, Stack, StackProps } from 'aws-cdk-lib';
import { StringParameter } from 'aws-cdk-lib/aws-ssm';
import { ProviderFunction } from '../../../../components/provider-function';
import { ApiGatewayConstruct, ApiGatewayConstructProps } from '../../../../components/api-gateway';
import { IQueue, Queue } from 'aws-cdk-lib/aws-sqs';
import { HttpMethod, HttpRoute, HttpRouteKey } from 'aws-cdk-lib/aws-apigatewayv2';
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import { InventoryFunction } from './constructs/functions/inventory';
import { NamedLambdaRole } from '../../../../components/named-lambda-role';
import { Role } from 'aws-cdk-lib/aws-iam';

export const FILEMANAGER_SERVICE_NAME = 'filemanager';

/**
 * Stateful config for filemanager.
 */
export type FilemanagerConfig = Omit<DatabaseProps, 'host' | 'securityGroup'> & {
  eventSourceQueueName: string;
  eventSourceBuckets: string[];
  inventorySourceBuckets: string[];
  databaseClusterEndpointHostParameter: string;
  vpcProps: VpcLookupOptions;
  migrateDatabase?: boolean;
  securityGroupName: string;
  fileManagerRoleName: string;
  apiGatewayCognitoProps: ApiGatewayConstructProps;
};

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
  readonly domainName: string;

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

    const role = this.createRole(props.fileManagerRoleName);
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

    this.createIngestFunction(props, role);
    this.createInventoryFunction(props, role);

    this.domainName = this.createApiFunction(props, role);
  }

  private createRole(name: string) {
    return new NamedLambdaRole(this, 'IngestFunctionRole', { name });
  }

  /**
   * Lambda function definitions and surrounding infrastructure.
   */
  private createIngestFunction(props: FilemanagerProps, role: Role) {
    return new IngestFunction(this, 'IngestFunction', {
      vpc: this.vpc,
      host: this.host,
      securityGroup: this.securityGroup,
      eventSources: [this.queue],
      buckets: props.eventSourceBuckets,
      role,
      ...props,
    });
  }

  /**
   * Create the inventory function.
   */
  private createInventoryFunction(props: FilemanagerProps, role: Role) {
    return new InventoryFunction(this, 'InventoryFunction', {
      vpc: this.vpc,
      host: this.host,
      securityGroup: this.securityGroup,
      port: props.port,
      buckets: props.inventorySourceBuckets,
      role,
    });
  }

  /**
   * Query function and API Gateway fronting the function. Returns the configured domain name.
   */
  private createApiFunction(props: FilemanagerProps, role: Role): string {
    let apiLambda = new ApiFunction(this, 'ApiFunction', {
      vpc: this.vpc,
      host: this.host,
      securityGroup: this.securityGroup,
      buckets: [...props.eventSourceBuckets, ...props.inventorySourceBuckets],
      role,
      ...props,
    });

    const apiGateway = new ApiGatewayConstruct(this, 'ApiGateway', props.apiGatewayCognitoProps);
    const httpApi = apiGateway.httpApi;

    const apiIntegration = new HttpLambdaIntegration('ApiIntegration', apiLambda.function);

    new HttpRoute(this, 'GetHttpRoute', {
      httpApi: httpApi,
      integration: apiIntegration,
      routeKey: HttpRouteKey.with('/{proxy+}', HttpMethod.GET),
    });

    new HttpRoute(this, 'PatchHttpRoute', {
      httpApi: httpApi,
      integration: apiIntegration,
      authorizer: apiGateway.authStackHttpLambdaAuthorizer,
      routeKey: HttpRouteKey.with('/{proxy+}', HttpMethod.PATCH),
    });

    new HttpRoute(this, 'PostHttpRoute', {
      httpApi: httpApi,
      integration: apiIntegration,
      authorizer: apiGateway.authStackHttpLambdaAuthorizer,
      routeKey: HttpRouteKey.with('/{proxy+}', HttpMethod.POST),
    });

    return apiGateway.domainName;
  }
}
