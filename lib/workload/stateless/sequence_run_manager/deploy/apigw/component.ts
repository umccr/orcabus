import { Construct } from 'constructs';
import { aws_ssm, Duration } from 'aws-cdk-lib';
import { HttpJwtAuthorizer } from 'aws-cdk-lib/aws-apigatewayv2-authorizers';
import { CorsHttpMethod, HttpApi } from 'aws-cdk-lib/aws-apigatewayv2';
import { IStringParameter } from 'aws-cdk-lib/aws-ssm';

export class SRMApiGatewayConstruct extends Construct {
  private readonly _httpApi: HttpApi;

  constructor(scope: Construct, id: string, apiName: string, region: string) {
    super(scope, id);

    this._httpApi = new HttpApi(this, id + 'HttpApi', {
      apiName: 'OrcaBusAPI' + apiName,
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
      defaultAuthorizer: this.getAuthorizer(id, region),
      // defaultDomainMapping: ... TODO
    });

    // TODO Configure access logging. See https://github.com/aws/aws-cdk/issues/11100

    // TODO setup cloud map service discovery perhaps
  }

  private getAuthorizer(id: string, region: string): HttpJwtAuthorizer {
    /**
     * FIXME One fine day in future when we have proper Cognito AAI setup.
     *  For the moment, we leverage Portal and established Cognito infrastructure.
     *  See https://github.com/umccr/orcabus/issues/102
     */
    const SSM_USER_POOL_ID: string = '/data_portal/client/cog_user_pool_id';
    const SSM_PORTAL_CLIENT_ID: string = '/data_portal/client/data2/cog_app_client_id_stage';  // i.e. JWT from UI client https://portal.[dev|stg|prod].umccr.org
    const SSM_STATUS_PAGE_CLIENT_ID: string = '/data_portal/status_page/cog_app_client_id_stage';  // i.e. JWT from UI client https://status.[dev|stg|prod].umccr.org

    const userPoolIdParam: IStringParameter = aws_ssm.StringParameter.fromStringParameterName(this, id + 'CognitoUserPoolIdParameter', SSM_USER_POOL_ID);
    const portalClientIdParam: IStringParameter = aws_ssm.StringParameter.fromStringParameterName(this, id + 'CognitoPortalClientIdParameter', SSM_PORTAL_CLIENT_ID);
    const statusPageClientIdParam: IStringParameter = aws_ssm.StringParameter.fromStringParameterName(this, id + 'CognitoStatusPageClientIdParameter', SSM_STATUS_PAGE_CLIENT_ID);

    const issuer = 'https://cognito-idp.' + region + '.amazonaws.com/' + userPoolIdParam.stringValue;

    return new HttpJwtAuthorizer(id + 'PortalAuthorizer', issuer, {
      jwtAudience: [
        portalClientIdParam.stringValue,
        statusPageClientIdParam.stringValue,
      ],
    });
  }

  get httpApi(): HttpApi {
    return this._httpApi;
  }
}
