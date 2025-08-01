import { Construct } from 'constructs';
import { aws_ssm, Duration, RemovalPolicy } from 'aws-cdk-lib';
import {
  HttpJwtAuthorizer,
  HttpLambdaAuthorizer,
  HttpLambdaResponseType,
} from 'aws-cdk-lib/aws-apigatewayv2-authorizers';
import { CfnStage, CorsHttpMethod, DomainName, HttpApi } from 'aws-cdk-lib/aws-apigatewayv2';
import { Certificate } from 'aws-cdk-lib/aws-certificatemanager';
import { IStringParameter, StringParameter } from 'aws-cdk-lib/aws-ssm';
import { LogGroup, RetentionDays } from 'aws-cdk-lib/aws-logs';
import { ARecord, HostedZone, RecordTarget } from 'aws-cdk-lib/aws-route53';
import { Role, ServicePrincipal } from 'aws-cdk-lib/aws-iam';
import { Function } from 'aws-cdk-lib/aws-lambda';
import { ApiGatewayv2DomainProperties } from 'aws-cdk-lib/aws-route53-targets';
import { authStackHttpLambdaAuthorizerParameterName } from '../../../../config/constants';

export interface ApiGwLogsConfig {
  /**
   * The number of days log events are kept in CloudWatch Logs.
   */
  retention: RetentionDays;
  /**
   * The removal policy to apply to the log group.
   */
  removalPolicy: RemovalPolicy;
}

export interface ApiGatewayConstructProps {
  /**
   * The AWS region.
   */
  region: string;
  /**
   * The name of the API.
   */
  apiName: string;
  /**
   * The prefix for the custom domain name
   */
  customDomainNamePrefix: string;
  /**
   *The cognito user pool id parameter name.
   */
  cognitoUserPoolIdParameterName: string;
  /**
   * The parameter name for the cognito client id in array.
   * In order API Gateway to validate the JWT token, it needs to know the client id which usually
   * stored in SSM Parameter. This will accept multiple parameter name in an array.
   */
  cognitoClientIdParameterNameArray: string[];
  /**
   * The configuration for aws cloudwatch logs
   */
  apiGwLogsConfig: ApiGwLogsConfig;
  /**
   * Allowed CORS origins.
   */
  corsAllowOrigins: string[];
}

export class ApiGatewayConstruct extends Construct {
  private readonly _httpApi: HttpApi;
  private readonly _domainName: string;
  readonly authStackHttpLambdaAuthorizer: HttpLambdaAuthorizer;

  constructor(scope: Construct, id: string, props: ApiGatewayConstructProps) {
    super(scope, id);

    // umccr acm arn
    const umccrAcmArn = StringParameter.valueForStringParameter(this, '/umccr/certificate_arn');
    const hostedDomainName = ApiGatewayConstruct.hostedDomainName(this);
    const hostedZoneId = StringParameter.valueForStringParameter(this, '/hosted_zone/umccr/id');

    this._domainName = `${props.customDomainNamePrefix}.${hostedDomainName}`;
    const apiGWDomainName = new DomainName(this, 'UmccrDomainName', {
      domainName: this.domainName,
      certificate: Certificate.fromCertificateArn(this, 'cert', umccrAcmArn),
    });

    this._httpApi = new HttpApi(this, 'HttpApi', {
      apiName: 'OrcaBusAPI-' + props.apiName,
      corsPreflight: {
        allowHeaders: [
          'content-type',
          'content-disposition',
          'authorization',
          'x-amz-date',
          'x-api-key',
          'x-amz-security-token',
          'x-amz-user-agent',
        ],
        allowMethods: [
          CorsHttpMethod.GET,
          CorsHttpMethod.HEAD,
          CorsHttpMethod.OPTIONS,
          CorsHttpMethod.POST,
          CorsHttpMethod.PATCH,
          CorsHttpMethod.DELETE,
        ],
        allowOrigins: props.corsAllowOrigins,
        maxAge: Duration.days(10),
      },
      defaultAuthorizer: this.getJWTAuthorizer(props),
      defaultDomainMapping: {
        domainName: apiGWDomainName,
      },
    });

    this.authStackHttpLambdaAuthorizer = this.getAuthStackHTTPLambdaAuthorizer(
      authStackHttpLambdaAuthorizerParameterName
    );

    new ARecord(this, 'CustomDomainARecord', {
      zone: HostedZone.fromHostedZoneAttributes(this, 'UmccrHostedZone', {
        hostedZoneId,
        zoneName: hostedDomainName,
      }),
      recordName: this.domainName,
      target: RecordTarget.fromAlias(
        new ApiGatewayv2DomainProperties(
          apiGWDomainName.regionalDomainName,
          apiGWDomainName.regionalHostedZoneId
        )
      ),
    });

    // LogGroups
    this.setupAccessLogs(props.apiGwLogsConfig);

    // CloudMap
    // this.setupCloudServiceDiscovery()
  }

  // TODO: https://github.com/aws-samples/aws-cdk-service-discovery-example/tree/main
  // private setupCloudServiceDiscovery() {
  // }

  // TODO: Taken from https://github.com/aws/aws-cdk/issues/11100#issuecomment-904627081
  // Monitor for higher level CDK construct instead of leveraging CfnStage
  private setupAccessLogs(props: ApiGwLogsConfig) {
    const accessLogs = new LogGroup(this, 'ApiGwAccessLogs', {
      retention: props.retention,
      removalPolicy: props.removalPolicy,
    });
    const stage = this.httpApi.defaultStage?.node.defaultChild as CfnStage;
    stage.accessLogSettings = {
      destinationArn: accessLogs.logGroupArn,
      format: JSON.stringify({
        requestId: '$context.requestId',
        userAgent: '$context.identity.userAgent',
        sourceIp: '$context.identity.sourceIp',
        requestTime: '$context.requestTime',
        requestTimeEpoch: '$context.requestTimeEpoch',
        httpMethod: '$context.httpMethod',
        path: '$context.path',
        status: '$context.status',
        protocol: '$context.protocol',
        responseLength: '$context.responseLength',
        domainName: '$context.domainName',
      }),
    };

    // Allow writing access logs, managed
    const role = new Role(this, 'AmazonAPIGatewayPushToCloudWatchLogs', {
      assumedBy: new ServicePrincipal('apigateway.amazonaws.com'),
    });

    accessLogs.grantWrite(role);
  }

  private getJWTAuthorizer(props: ApiGatewayConstructProps): HttpJwtAuthorizer {
    /**
     * FIXME One fine day in future when we have proper Cognito AAI setup.
     *  For the moment, we leverage Portal and established Cognito infrastructure.
     *  See https://github.com/umccr/orcabus/issues/102
     */

    const userPoolIdParam: IStringParameter = aws_ssm.StringParameter.fromStringParameterName(
      this,
      'CognitoUserPoolIdParameter',
      props.cognitoUserPoolIdParameterName
    );

    const clientIdParamsArray: IStringParameter[] = props.cognitoClientIdParameterNameArray.map(
      (name) =>
        aws_ssm.StringParameter.fromStringParameterName(
          this,
          `CognitoClientId${name}Parameter`,
          name
        )
    );

    const issuer =
      'https://cognito-idp.' + props.region + '.amazonaws.com/' + userPoolIdParam.stringValue;

    return new HttpJwtAuthorizer('PortalAuthorizer', issuer, {
      jwtAudience: clientIdParamsArray.map((param) => param.stringValue),
    });
  }

  /**
   * Get the HTTP Lambda Authorizer defined in the authorization stack manager
   * @param authStackHttpLambdaAuthorizerParameterName The SSM Parameter Name that stores the ARN of the lambda authorizer
   * @returns
   */
  private getAuthStackHTTPLambdaAuthorizer(authStackHttpLambdaAuthorizerParameterName: string) {
    const lambdaArn = StringParameter.valueForStringParameter(
      this,
      authStackHttpLambdaAuthorizerParameterName
    );

    // Get the lambda HTTP authorizer defined in the authorization stack manager
    const lambdaAuthorizer = Function.fromFunctionAttributes(
      this,
      'AuthStackHTTPLambdaAuthorizer',
      {
        functionArn: lambdaArn,
        sameEnvironment: true,
      }
    );

    return new HttpLambdaAuthorizer('AuthStackLambdaHttpAuthorizer', lambdaAuthorizer, {
      authorizerName: 'AuthStackHTTPLambdaAuthorizer',
      responseTypes: [HttpLambdaResponseType.SIMPLE],
    });
  }

  get httpApi(): HttpApi {
    return this._httpApi;
  }

  get domainName(): string {
    return this._domainName;
  }

  /**
   * Get the domain name for the UMCCR hosted zone.
   */
  static hostedDomainName(scope: Construct): string {
    return StringParameter.valueForStringParameter(scope, '/hosted_zone/umccr/name');
  }
}
