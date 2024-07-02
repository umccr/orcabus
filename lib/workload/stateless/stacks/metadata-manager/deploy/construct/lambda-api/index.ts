import { Construct } from 'constructs';
import { Duration } from 'aws-cdk-lib';
import { HttpMethod, HttpRoute, HttpRouteKey, IHttpApi } from 'aws-cdk-lib/aws-apigatewayv2';
import { PythonFunction, PythonFunctionProps } from '@aws-cdk/aws-lambda-python-alpha';
import { ISecret } from 'aws-cdk-lib/aws-secretsmanager';
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import {
  ApiGatewayConstruct,
  ApiGatewayConstructProps,
} from '../../../../../../components/api-gateway';
import { ApiGatewayProxyIntegration } from '../../../../../../components/api-gateway-proxy-integration';

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

    this.lambda = new PythonFunction(this, 'APILambda', {
      ...lambdaProps.basicLambdaConfig,
      index: 'handler/api.py',
      handler: 'handler',
      timeout: Duration.seconds(28),
    });
    lambdaProps.dbConnectionSecret.grantRead(this.lambda);

    new ApiGatewayProxyIntegration(this, 'OrcaBusAPI-MetadataManager', {
      handler: this.lambda,
      apiGatewayProps: lambdaProps.apiGatewayConstructProps,
    });
  }
}
