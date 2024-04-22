import { Construct } from 'constructs';
import { aws_ssm, Duration } from 'aws-cdk-lib';
import { HttpJwtAuthorizer } from 'aws-cdk-lib/aws-apigatewayv2-authorizers';
import { CorsHttpMethod, HttpApi } from 'aws-cdk-lib/aws-apigatewayv2';
import { IStringParameter } from 'aws-cdk-lib/aws-ssm';

export interface ApiGatewayConstructProps {
  region: string;
  cognitoUserPoolIdParameterName: string;
  cognitoPortalAppClientIdParameterName: string;
  cognitoStatusPageAppClientIdParameterName: string;
}

export class ApiGatewayConstruct extends Construct {
  private readonly _httpApi: HttpApi;

  constructor(scope: Construct, id: string, props: ApiGatewayConstructProps) {
    super(scope, id);

    this._httpApi = new HttpApi(this, 'HttpApi', {
      apiName: 'OrcaBusAPI-${service}', // FIXME: Props this from construct user
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
      defaultAuthorizer: this.getAuthorizer(props),
      // defaultDomainMapping: ... TODO
    });

    // TODO Configure access logging. See https://github.com/aws/aws-cdk/issues/11100

    // TODO setup cloud map service discovery perhaps
  }

  private getAuthorizer(props: ApiGatewayConstructProps): HttpJwtAuthorizer {
    /**
     * FIXME One fine day in future when we have proper Cognito AAI setup.
     *  For the moment, we leverage Portal and established Cognito infrastructure.
     *  See https://github.com/umccr/orcabus/issues/102
     *
     * UI clients:
     *  https://portal.[dev|stg|prod].umccr.org
     *  https://status.[dev|stg|prod].umccr.org
     */

    const userPoolIdParam: IStringParameter = aws_ssm.StringParameter.fromStringParameterName(
      this,
      'CognitoUserPoolIdParameter',
      props.cognitoUserPoolIdParameterName
    );
    const portalClientIdParam: IStringParameter = aws_ssm.StringParameter.fromStringParameterName(
      this,
      'CognitoPortalClientIdParameter',
      props.cognitoPortalAppClientIdParameterName
    );
    const statusPageClientIdParam: IStringParameter =
      aws_ssm.StringParameter.fromStringParameterName(
        this,
        'CognitoStatusPageClientIdParameter',
        props.cognitoStatusPageAppClientIdParameterName
      );

    const issuer =
      'https://cognito-idp.' + props.region + '.amazonaws.com/' + userPoolIdParam.stringValue;

    return new HttpJwtAuthorizer('PortalAuthorizer', issuer, {
      jwtAudience: [portalClientIdParam.stringValue, statusPageClientIdParam.stringValue],
    });
  }

  get httpApi(): HttpApi {
    return this._httpApi;
  }
}
