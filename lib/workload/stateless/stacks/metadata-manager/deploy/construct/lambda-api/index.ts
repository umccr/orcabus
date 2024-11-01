import { Construct } from 'constructs';
import { Duration } from 'aws-cdk-lib';
import { Function } from 'aws-cdk-lib/aws-lambda';
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
  /**
   * sync db from gsheet lambda
   */
  syncGsheetLambda: Function;
  /**
   * sync db from csv file lambda
   */
  syncCustomCsvLambda: Function;
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
      routeKey: HttpRouteKey.with('/{PROXY+}', HttpMethod.GET),
    });

    new HttpRoute(this, 'ApiLambdaHttpRoutePost', {
      httpApi: apiGW.httpApi,
      integration: apiIntegration,
      routeKey: HttpRouteKey.with('/{PROXY+}', HttpMethod.POST),
    });

    // Would need to add permission and env-var for the sync lambdas
    lambdaProps.syncGsheetLambda.grantInvoke(this.lambda);
    this.lambda.addEnvironment(
      'SYNC_GSHEET_LAMBDA_NAME',
      lambdaProps.syncGsheetLambda.functionName
    );

    lambdaProps.syncCustomCsvLambda.grantInvoke(this.lambda);
    this.lambda.addEnvironment(
      'SYNC_CSV_PRESIGNED_URL_LAMBDA_NAME',
      lambdaProps.syncCustomCsvLambda.functionName
    );
  }
}
