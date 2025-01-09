import { Construct } from 'constructs';
import { Duration, Stack, StackProps } from 'aws-cdk-lib';
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import { HttpMethod, HttpRoute, HttpRouteKey } from 'aws-cdk-lib/aws-apigatewayv2';

import { ApiGatewayConstruct, ApiGatewayConstructProps } from '../../../components/api-gateway';
import path from 'path';
import { Architecture, DockerImageCode, DockerImageFunction } from 'aws-cdk-lib/aws-lambda';
import { StringParameter } from 'aws-cdk-lib/aws-ssm';

export interface SampleSheetCheckerStackProps {
  /**
   * The props for api-gateway
   */
  apiGatewayConstructProps: ApiGatewayConstructProps;
}

export class SampleSheetCheckerStack extends Stack {
  constructor(scope: Construct, id: string, props: StackProps & SampleSheetCheckerStackProps) {
    super(scope, id, props);

    const apiGW = new ApiGatewayConstruct(
      this,
      'OrcaBusAPI-SampleSheetChecker',
      props.apiGatewayConstructProps
    );

    const domainName = StringParameter.valueForStringParameter(this, 'umccr_domain');

    const sscheckLambda = new DockerImageFunction(this, 'SSCheckLambda', {
      code: DockerImageCode.fromImageAsset(path.join(__dirname, 'sample-sheet-check-lambda'), {
        file: 'lambda.Dockerfile',
      }),
      architecture: Architecture.ARM_64,
      timeout: Duration.seconds(28),
      memorySize: 1024,
      environment: {
        DATA_PORTAL_DOMAIN_NAME: domainName,
      },
    });

    // add some integration to the http api gw
    const apiIntegration = new HttpLambdaIntegration('ApiLambdaIntegration', sscheckLambda);

    // Routes for API schemas
    new HttpRoute(this, 'PostHttpRoute', {
      httpApi: apiGW.httpApi,
      integration: apiIntegration,
      routeKey: HttpRouteKey.with(`/{PROXY+}`, HttpMethod.POST),
    });
  }
}
