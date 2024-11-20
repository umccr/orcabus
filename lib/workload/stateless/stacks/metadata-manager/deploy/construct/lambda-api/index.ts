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
  private readonly API_VERSION = 'v1';

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
      // The optimum memory from lambda power tuning tool (Result based on enforcing cold start)
      // https://lambda-power-tuning.show/#gAAAAQACAAQABgAI;ulPPRclpmUU0UHpFIoxhRT3aVkVGyk9F;XJ7INgXRyTZLUMM2DoLGNpPG0DZMo/42
      memorySize: 1024,
    });
    lambdaProps.dbConnectionSecret.grantRead(this.lambda);

    // add some integration to the http api gw
    const apiIntegration = new HttpLambdaIntegration('ApiLambdaIntegration', this.lambda);

    new HttpRoute(this, 'GetHttpRoute', {
      httpApi: apiGW.httpApi,
      integration: apiIntegration,
      routeKey: HttpRouteKey.with(`/api/${this.API_VERSION}/{PROXY+}`, HttpMethod.GET),
    });

    // Add permission, HTTP route, and env-var for the sync lambdas

    lambdaProps.syncGsheetLambda.grantInvoke(this.lambda);
    this.lambda.addEnvironment(
      'SYNC_GSHEET_LAMBDA_NAME',
      lambdaProps.syncGsheetLambda.functionName
    );
    new HttpRoute(this, 'PostHttpRouteSyncGsheet', {
      httpApi: apiGW.httpApi,
      integration: apiIntegration,
      routeKey: HttpRouteKey.with(`/api/${this.API_VERSION}/sync/gsheet/{PROXY+}`, HttpMethod.POST),
    });

    lambdaProps.syncCustomCsvLambda.grantInvoke(this.lambda);
    this.lambda.addEnvironment(
      'SYNC_CSV_PRESIGNED_URL_LAMBDA_NAME',
      lambdaProps.syncCustomCsvLambda.functionName
    );
    new HttpRoute(this, 'PostHttpRouteSyncPresignedCsv', {
      httpApi: apiGW.httpApi,
      integration: apiIntegration,
      // Only admin group can use this csv sync endpoint
      authorizer: apiGW.authStackHttpLambdaAuthorizer,
      routeKey: HttpRouteKey.with(
        `/api/${this.API_VERSION}/sync/presigned-csv/{PROXY+}`,
        HttpMethod.POST
      ),
    });
  }
}
