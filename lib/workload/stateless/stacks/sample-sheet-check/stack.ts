import { Construct } from 'constructs';
import { Duration, Stack, StackProps } from 'aws-cdk-lib';
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import { HttpMethod, HttpRoute, HttpRouteKey } from 'aws-cdk-lib/aws-apigatewayv2';

import { ApiGatewayConstruct, ApiGatewayConstructProps } from '../../../components/api-gateway';
import path from 'path';
import { Architecture, DockerImageCode, DockerImageFunction } from 'aws-cdk-lib/aws-lambda';
import { StringParameter } from 'aws-cdk-lib/aws-ssm';
import { RetentionDays } from 'aws-cdk-lib/aws-logs';
import { Effect, PolicyStatement } from 'aws-cdk-lib/aws-iam';

export interface SampleSheetCheckerStackProps {
  /**
   * The props for api-gateway
   */
  apiGatewayConstructProps: ApiGatewayConstructProps;
  /**
   * The domain name of the metadata service
   */
  metadataDomainName: string;
}

export class SampleSheetCheckerStack extends Stack {
  constructor(scope: Construct, id: string, props: StackProps & SampleSheetCheckerStackProps) {
    super(scope, id, props);

    const apiGW = new ApiGatewayConstruct(
      this,
      'OrcaBusAPI-SampleSheetChecker',
      props.apiGatewayConstructProps
    );

    const sscheckLambda = new DockerImageFunction(this, 'SSCheckLambda', {
      code: DockerImageCode.fromImageAsset(path.join(__dirname, 'sample-sheet-check-lambda'), {
        file: 'lambda.Dockerfile',
      }),
      logRetention: RetentionDays.TWO_WEEKS,
      architecture: Architecture.ARM_64,
      timeout: Duration.seconds(28),
      memorySize: 1024,
      environment: {
        METADATA_DOMAIN_NAME: props.metadataDomainName,
      },
      initialPolicy: [
        // Not enabling logs
        new PolicyStatement({
          effect: Effect.DENY,
          actions: ['logs:CreateLogGroup', 'logs:CreateLogStream', 'logs:PutLogEvents'],
          resources: ['arn:aws:logs:*:*:*'],
        }),
      ],
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
