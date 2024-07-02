import { Construct } from 'constructs';
import { HttpMethod, HttpRoute, HttpRouteKey } from 'aws-cdk-lib/aws-apigatewayv2';
import { ApiGatewayConstruct, ApiGatewayConstructProps } from '../api-gateway';
import { IFunction } from 'aws-cdk-lib/aws-lambda';
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';

/**
 * Props for the Lambda proxy integration construct.
 */
export interface ApiGatewayProxyIntegrationProps {
  /**
   * Lambda handler.
   */
  handler: IFunction;
  /**
   * Properties for the API gateway construct.
   */
  apiGatewayProps: ApiGatewayConstructProps;
}

/**
 * This class combines a Lambda handler with the `ApiGatewayConstruct` on a `/{proxy+}` route.
 */
export class ApiGatewayProxyIntegration extends Construct {
  readonly apiGateway: ApiGatewayConstruct;

  constructor(scope: Construct, id: string, props: ApiGatewayProxyIntegrationProps) {
    super(scope, id);

    this.apiGateway = new ApiGatewayConstruct(this, 'ApiGateway', props.apiGatewayProps);

    const integration = new HttpLambdaIntegration('ApiLambdaIntegration', props.handler);
    new HttpRoute(scope, id, {
      httpApi: this.apiGateway.httpApi,
      integration,
      routeKey: HttpRouteKey.with('/{proxy+}', HttpMethod.ANY),
    });
  }
}
