import { Construct } from 'constructs';
import { aws_ssm, Duration, RemovalPolicy } from 'aws-cdk-lib';
import { HttpJwtAuthorizer } from 'aws-cdk-lib/aws-apigatewayv2-authorizers';
import { CfnStage, CorsHttpMethod, DomainName, HttpApi } from 'aws-cdk-lib/aws-apigatewayv2';
import { Certificate } from 'aws-cdk-lib/aws-certificatemanager';
import { IStringParameter, StringParameter } from 'aws-cdk-lib/aws-ssm';
import { LogGroup, RetentionDays } from 'aws-cdk-lib/aws-logs';
import { ARecord, HostedZone, RecordTarget } from 'aws-cdk-lib/aws-route53';
import { Role, ServicePrincipal } from 'aws-cdk-lib/aws-iam';
import { ApiGatewayv2DomainProperties } from 'aws-cdk-lib/aws-route53-targets';

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
  region: string;
  apiName: string | undefined;
  cognitoUserPoolIdParameterName: string;
  cognitoPortalAppClientIdParameterName: string;
  cognitoStatusPageAppClientIdParameterName: string;
  /**
   * The prefix for the custom domain name
   */
  customDomainNamePrefix: string;
  /**
   * The configuration for aws cloudwatch logs
   */
  apiGwLogsConfig: ApiGwLogsConfig;
  /**
   * Allowed CORS origins.
   */
  corsAllowOrigins?: string[];
}

export class ApiGatewayConstruct extends Construct {
  private readonly _httpApi: HttpApi;

  constructor(scope: Construct, id: string, props: ApiGatewayConstructProps) {
    super(scope, id);

    // umccr acm arn
    const umccrAcmArn = StringParameter.valueForStringParameter(this, '/umccr/certificate_arn');
    const hostedDomainName = StringParameter.valueForStringParameter(
      this,
      '/hosted_zone/umccr/name'
    );
    const hostedZoneId = StringParameter.valueForStringParameter(this, '/hosted_zone/umccr/id');

    const domainName = `${props.customDomainNamePrefix}.${hostedDomainName}`;
    const apiGWDomainName = new DomainName(this, 'UmccrDomainName', {
      domainName: `${props.customDomainNamePrefix}.${hostedDomainName}`,
      certificate: Certificate.fromCertificateArn(this, 'cert', umccrAcmArn),
    });

    this._httpApi = new HttpApi(this, 'HttpApi', {
      apiName: 'OrcaBusAPI-' + props.apiName,
      corsPreflight: {
        allowHeaders: ['Authorization'],
        allowMethods: [
          CorsHttpMethod.GET,
          CorsHttpMethod.HEAD,
          CorsHttpMethod.OPTIONS,
          CorsHttpMethod.POST,
          CorsHttpMethod.PATCH,
        ],
        allowOrigins: props.corsAllowOrigins,
        maxAge: Duration.days(10),
      },
      defaultAuthorizer: this.getAuthorizer(props),
      defaultDomainMapping: {
        domainName: apiGWDomainName,
      },
    });

    new ARecord(this, 'CustomDomainARecord', {
      zone: HostedZone.fromHostedZoneAttributes(this, 'UmccrHostedZone', {
        hostedZoneId,
        zoneName: hostedDomainName,
      }),
      recordName: domainName,
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
