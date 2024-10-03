import { Construct } from 'constructs';
import { Duration } from 'aws-cdk-lib';
import { HttpMethod, HttpRoute, HttpRouteKey } from 'aws-cdk-lib/aws-apigatewayv2';
import { PythonFunction, PythonFunctionProps } from '@aws-cdk/aws-lambda-python-alpha';
import { ISecret } from 'aws-cdk-lib/aws-secretsmanager';
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import {
  ApiGatewayConstruct,
  ApiGatewayConstructProps,
} from '../../../../../../components/api-gateway';

type LambdaProps = {
  /**
   * The basic common lambda properties that it should inherit from
   */
  basicLambdaConfig: PythonFunctionProps;
  /**
   * The secret for the db connection where the lambda will need access to
   */
  dbConnectionSecret: ISecret;
  /**
   * The props for api-gateway
   */
  apiGatewayConstructProps: ApiGatewayConstructProps;
};

export class LambdaAPIConstruct extends Construct {
  private readonly lambda: PythonFunction;

  constructor(scope: Construct, id: string, lambdaProps: LambdaProps) {
    super(scope, id);

    const apiGW = new ApiGatewayConstruct(
      this,
      'OrcaBusAPI-MetadataManager',
      lambdaProps.apiGatewayConstructProps
    );

    this.lambda = new PythonFunction(this, 'APILambda', {
      ...lambdaProps.basicLambdaConfig,
      index: 'handler/api.py',
      handler: 'handler',
      timeout: Duration.seconds(28),
    });
    lambdaProps.dbConnectionSecret.grantRead(this.lambda);

    // add some integration to the http api gw
    const apiIntegration = new HttpLambdaIntegration('ApiLambdaIntegration', this.lambda);

    new HttpRoute(this, 'ApiLambdaHttpRoute', {
      httpApi: apiGW.httpApi,
      integration: apiIntegration,
      routeKey: HttpRouteKey.with('/{proxy+}', HttpMethod.GET),
    });
  }
}
