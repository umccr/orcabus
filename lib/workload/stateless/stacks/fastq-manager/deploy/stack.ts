import path from 'path';
import { Construct } from 'constructs';
import { Duration, Stack, StackProps } from 'aws-cdk-lib';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { ApiGatewayConstruct, ApiGatewayConstructProps } from '../../../../components/api-gateway';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';
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
import { MetadataToolsPythonLambdaLayer } from '../../../../components/python-metadata-tools-layer';

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

  dynamodbTableName: string;
  dynamodbIndexes: string[];
}

export type FastqManagerStackProps = FastqManagerStackConfig & cdk.StackProps;

export class FastqManagerStack extends Stack {
  public readonly API_VERSION = 'v1';

  constructor(scope: Construct, id: string, props: StackProps & FastqManagerStackProps) {
    super(scope, id, props);

    const dynamodbTable = dynamodb.TableV2.fromTableName(
      this,
      'dynamodb_table',
      props.dynamodbTableName
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
    const metadataLayer = new MetadataToolsPythonLambdaLayer(this, 'metadata-tools-layer', {
      layerPrefix: 'fqm',
    });

    /*
    Collect the required secret and ssm parameters for getting metadata
    */
    const hostnameSsmParameterObj = ssm.StringParameter.fromStringParameterName(
      this,
      'hostname_ssm_parameter',
      props.hostedZoneNameSsmParameterPath
    );
    const orcabusTokenSecretObj = secretsmanager.Secret.fromSecretNameV2(
      this,
      'orcabus_token_secret',
      props.orcabusTokenSecretsManagerPath
    );

    // Api handler function
    const lambdaFunction = new PythonFunction(this, 'FastqManagerApi', {
      entry: path.join(__dirname, '../app'),
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      index: 'handler.py',
      handler: 'handler',
      timeout: Duration.seconds(60),
      memorySize: 2048,
      environment: {
        DYNAMODB_FASTQ_LIST_ROW_TABLE_NAME: dynamodbTable.tableName,
        DYNAMODB_HOST: `https://dynamodb.${this.region}.amazonaws.com`,
        HOSTNAME_SSM_PARAMETER: hostnameSsmParameterObj.parameterName,
        ORCABUS_TOKEN_SECRET_ID: orcabusTokenSecretObj.secretName,
      },
      layers: [metadataLayer.lambdaLayerVersionObj, fileManagerLayer.lambdaLayerVersionObj],
    });

    // Give lambda function permissions to secrets and ssm parameters
    orcabusTokenSecretObj.grantRead(lambdaFunction);
    hostnameSsmParameterObj.grantRead(lambdaFunction);

    // Allow read/write access to the dynamodb table
    dynamodbTable.grantReadWriteData(lambdaFunction);

    // Grant query permissions on indexes
    const index_arn_list: string[] = props.dynamodbIndexes.map((index_name) => {
      return `arn:aws:dynamodb:${this.region}:${this.account}:table/${props.dynamodbTableName}/index/${index_name}-index`;
    });
    lambdaFunction.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['dynamodb:Query'],
        resources: index_arn_list,
      })
    );

    const apiGateway = new ApiGatewayConstruct(this, 'ApiGateway', props.apiGatewayCognitoProps);
    const apiIntegration = new HttpLambdaIntegration('ApiIntegration', lambdaFunction);

    // Routes for API schemas
    this.add_http_routes(apiGateway, apiIntegration);
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
