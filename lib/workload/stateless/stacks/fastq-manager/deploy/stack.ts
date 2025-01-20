import path from 'path';
import { Construct } from 'constructs';
import { Duration, Stack, StackProps } from 'aws-cdk-lib';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { ApiGatewayConstruct, ApiGatewayConstructProps } from '../../../../components/api-gateway';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import {
  HttpMethod,
  HttpNoneAuthorizer,
  HttpRoute,
  HttpRouteKey,
} from 'aws-cdk-lib/aws-apigatewayv2';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { FilemanagerToolsPythonLambdaLayer } from '../../../../components/python-filemanager-tools-layer';
import * as cdk from 'aws-cdk-lib';
import { LAMBDA_HELPER_FUNCTION_NAMES } from './constants';

export interface FastqManagerStackConfig {
  /*
  API Gateway props
  */
  apiGatewayCognitoProps: ApiGatewayConstructProps;

  /*
  Orcabus token and zone name for external lambda functions
  */
  orcabusTokenSecretsManagerPath: string;
  hostedZoneNameSsmParameterPath: string;
}

export type FastqManagerStackProps = FastqManagerStackConfig & cdk.StackProps;

export class FastqManagerStack extends Stack {
  public readonly API_VERSION = 'v1';

  constructor(scope: Construct, id: string, props: StackProps & FastqManagerStackProps) {
    super(scope, id, props);

    // Api handler function
    const lambdaFunction = new PythonFunction(this, 'FastqManagerApi', {
      entry: path.join(__dirname, '../app'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'main.py',
      handler: 'handler',
      timeout: Duration.seconds(60),
      memorySize: 2048,
    });

    const apiGateway = new ApiGatewayConstruct(this, 'ApiGateway', props.apiGatewayCognitoProps);
    const apiIntegration = new HttpLambdaIntegration('ApiIntegration', lambdaFunction);

    // Routes for API schemas
    this.add_http_routes(apiGateway, apiIntegration);

    // Build lambda helper functions
    const lambdaHelperFunctions = this.add_lambda_helper_functions(
      props.hostedZoneNameSsmParameterPath,
      props.orcabusTokenSecretsManagerPath
    );

    // Grant lambda helper functions permissions to access resources
    lambdaHelperFunctions.forEach((lambdaHelperFunction) => {
      lambdaHelperFunction.currentVersion.grantInvoke(lambdaFunction);
    });
  }

  // Add lambda helper functions
  private add_lambda_helper_functions(
    hostnameSsmParameterPath: string,
    orcabusTokenSecretId: string
  ): PythonFunction[] {
    /*
    Collect the required secret and ssm parameters for getting metadata
    */
    const hostnameSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'hostname_ssm_parameter',
      hostnameSsmParameterPath
    );
    const orcabusTokenSecretObj = secretsmanager.Secret.fromSecretNameV2(
      this,
      'orcabus_token_secret',
      orcabusTokenSecretId
    );

    // Create the FileManager Tool Layer
    const fileManagerLayer = new FilemanagerToolsPythonLambdaLayer(
      this,
      'filemanager-tools-layer',
      {
        layerPrefix: 'fqm',
      }
    );

    // Create the Metadata tool layer
    const metadataLayer = new FilemanagerToolsPythonLambdaLayer(this, 'metadata-tools-layer', {
      layerPrefix: 'fqm',
    });

    // Iterate through LAMBDA_HELPER_FUNCTION_NAMES and generate a lambda function for each
    const lambdaFunctionObjects: PythonFunction[] = [];
    for (const lambdaHelperFunctionName of LAMBDA_HELPER_FUNCTION_NAMES) {
      lambdaFunctionObjects.push(
        new PythonFunction(this, lambdaHelperFunctionName, {
          entry: path.join(__dirname, '../lambdas', lambdaHelperFunctionName),
          runtime: lambda.Runtime.PYTHON_3_12,
          architecture: lambda.Architecture.ARM_64,
          index: `${lambdaHelperFunctionName}.py`,
          handler: 'handler',
          timeout: Duration.seconds(60),
          memorySize: 2048,
          environment: {
            HOSTNAME_SSM_PARAMETER: hostnameSsmParameterObj.parameterName,
            ORCABUS_TOKEN_SECRET_ID: orcabusTokenSecretObj.secretName,
          },
          layers: [fileManagerLayer.lambdaLayerVersionObj, metadataLayer.lambdaLayerVersionObj],
        })
      );
    }

    // Add permissions to each of the lambda function objects
    lambdaFunctionObjects.forEach((lambdaFunctionObject) => {
      hostnameSsmParameterObj.grantRead(lambdaFunctionObject.currentVersion);
      orcabusTokenSecretObj.grantRead(lambdaFunctionObject.currentVersion);
    });

    return lambdaFunctionObjects;
  }

  // Add the http routes to the API Gateway
  private add_http_routes(apiGateway: ApiGatewayConstruct, apiIntegration: HttpLambdaIntegration) {
    // Routes for API schemas
    new HttpRoute(this, 'GetSchemaHttpRoute', {
      httpApi: apiGateway.httpApi,
      integration: apiIntegration,
      authorizer: new HttpNoneAuthorizer(), // No auth needed for schema
      routeKey: HttpRouteKey.with(`/schema/{PROXY+}`, HttpMethod.GET),
    });
    new HttpRoute(this, 'GetHttpRoute', {
      httpApi: apiGateway.httpApi,
      integration: apiIntegration,
      routeKey: HttpRouteKey.with(`/api/${this.API_VERSION}/{PROXY+}`, HttpMethod.GET),
    });
    new HttpRoute(this, 'PostHttpRoute', {
      httpApi: apiGateway.httpApi,
      integration: apiIntegration,
      authorizer: apiGateway.authStackHttpLambdaAuthorizer,
      routeKey: HttpRouteKey.with(`/api/${this.API_VERSION}/{PROXY+}`, HttpMethod.POST),
    });
    new HttpRoute(this, 'PatchHttpRoute', {
      httpApi: apiGateway.httpApi,
      integration: apiIntegration,
      authorizer: apiGateway.authStackHttpLambdaAuthorizer,
      routeKey: HttpRouteKey.with(`/api/${this.API_VERSION}/{PROXY+}`, HttpMethod.PATCH),
    });
    new HttpRoute(this, 'DeleteHttpRoute', {
      httpApi: apiGateway.httpApi,
      integration: apiIntegration,
      authorizer: apiGateway.authStackHttpLambdaAuthorizer,
      routeKey: HttpRouteKey.with(`/api/${this.API_VERSION}/{PROXY+}`, HttpMethod.DELETE),
    });
  }
}
