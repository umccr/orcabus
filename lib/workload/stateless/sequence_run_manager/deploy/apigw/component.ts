import { Construct } from 'constructs';
import { aws_ssm, Duration } from 'aws-cdk-lib';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import { HttpUserPoolAuthorizer } from 'aws-cdk-lib/aws-apigatewayv2-authorizers';
import { CorsHttpMethod, HttpApi } from 'aws-cdk-lib/aws-apigatewayv2';
import { IStringParameter } from 'aws-cdk-lib/aws-ssm';

export class SRMApiGatewayConstruct extends Construct {
  private readonly SSM_USER_POOL_ID: string = '/data_portal/client/cog_user_pool_id'; // FIXME one fine day in future
  private readonly _httpApi: HttpApi;

  constructor(scope: Construct, id: string) {
    super(scope, id);

    const userPoolParam: IStringParameter = aws_ssm.StringParameter.fromStringParameterName(this, id + 'SSMStringParameter', this.SSM_USER_POOL_ID);
    const userPool = cognito.UserPool.fromUserPoolId(scope, id + 'UserPool', userPoolParam.stringValue);

    this._httpApi = new HttpApi(this, id + 'HttpApi', {
      apiName: 'OrcaBus SequenceRunManager API',
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

    // TODO setup cloud map service discovery perhaps
  }

  get httpApi(): HttpApi {
    return this._httpApi;
  }
}
