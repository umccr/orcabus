import { Construct } from 'constructs';
import { aws_ssm, Duration } from 'aws-cdk-lib';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import { HttpUserPoolAuthorizer } from 'aws-cdk-lib/aws-apigatewayv2-authorizers';
import { SHARED_HTTP_API_ID } from '../../../../config/param';
import { CorsHttpMethod, HttpApi } from 'aws-cdk-lib/aws-apigatewayv2';

export class SharedApiGatewayConstruct extends Construct {
  private readonly SSM_USER_POOL_ID: string = '/data_portal/client/cog_user_pool_id'; // FIXME one fine day in future

  constructor(scope: Construct, id: string) {
    super(scope, id);

    const userPoolId: string = aws_ssm.StringParameter.valueFromLookup(this, this.SSM_USER_POOL_ID);
    const userPool = cognito.UserPool.fromUserPoolId(this, id, userPoolId);

    const httpApi = new HttpApi(this, id + 'HttpApi', {
      apiName: 'OrcaBusSharedAPI',
      corsPreflight: {
        allowHeaders: ['Authorization'],
        allowMethods: [
          CorsHttpMethod.GET,
          CorsHttpMethod.HEAD,
          CorsHttpMethod.OPTIONS,
          CorsHttpMethod.POST,
        ],
        allowOrigins: ['*'], // FIXME allowed origins from config constant
        maxAge: Duration.days(10),
      },
      defaultAuthorizer: new HttpUserPoolAuthorizer(id + 'HttpUserPoolAuthorizer', userPool),
      // defaultDomainMapping: ... TODO
    });

    new aws_ssm.StringParameter(this, 'sharedHttpApiIdParameter', {
      description: 'OrcaBus Shared API Gateway httpApiId',
      parameterName: SHARED_HTTP_API_ID,
      stringValue: httpApi.httpApiId,
    });

    // TODO setup cloud map service discovery perhaps
  }
}
