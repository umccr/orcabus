import {
  RemovalPolicy,
  aws_ec2 as ec2,
  aws_secretsmanager as secretsmanager,
  aws_lambda as lambda,
  aws_ssm as ssm,
  aws_events as events,
  aws_events_targets as targets,
  Duration,
} from 'aws-cdk-lib';
import * as path from 'path';
import { Construct } from 'constructs';
import { ISecurityGroup } from 'aws-cdk-lib/aws-ec2';
import { HttpLambdaIntegration } from '@aws-cdk/aws-apigatewayv2-integrations-alpha';
import { CorsHttpMethod, HttpApi, HttpMethod } from '@aws-cdk/aws-apigatewayv2-alpha';

export interface appProps {
  edgedDb: {
    dsnNoPassword: string;
    secret: secretsmanager.ISecret;
    securityGroup: ISecurityGroup;
  };
  network: {
    vpc: ec2.IVpc;
    apiGatewayHttpApiId?: string;
  };
  configuration: appConfigurationProps;
}

export interface appConfigurationProps {
  triggerLoadSchedule: events.Schedule;
}

/**
 * A construct wrapping an installation of EdgeDb as a service (assuming
 * an existing RDS postgres).
 */
export class AppConstruct extends Construct {
  constructor(scope: Construct, id: string, props: appProps) {
    super(scope, id);

    // edgedb environment to make connection the edgedb instance
    const edgedbConnectionEnv = {
      EDGEDB_DSN: props.edgedDb.dsnNoPassword,
      EDGEDB_CLIENT_TLS_SECURITY: 'insecure',
      METADATA_MANAGER_EDGEDB_SECRET_NAME: props.edgedDb.secret.secretName,
    };

    // Lambda would need to access Secret Manager to retrieve edgeDb password
    // thus need an outbound traffic from SG to secret manager
    const outboundSG = new ec2.SecurityGroup(this, 'OutboundSecurityGroup', {
      vpc: props.network.vpc,
      allowAllOutbound: true,
      description:
        'Security group that allows the app service to reach out over the network (e.g. secret manager)',
    });

    // the layer for lambdas which usually be dependency across lambdas
    const dependencyLayer = new lambda.LayerVersion(this, 'DependencyLayer', {
      removalPolicy: RemovalPolicy.DESTROY,
      code: lambda.Code.fromAsset(path.join(__dirname, '../../../asset/dependency.zip')),
      compatibleArchitectures: [lambda.Architecture.ARM_64],
    });

    // lambda would need access to edgeDb secret manager password
    // environment variable in lambda does not integrate with value stored in secret
    // but AWS has an extension to fetch secret by importing AWS lambda layer
    // Ref: https://docs.aws.amazon.com/secretsmanager/latest/userguide/retrieving-secrets_lambda.html
    const awsSecretLambdaLayerExtension = lambda.LayerVersion.fromLayerVersionArn(
      this,
      'LambdaLayerSecretExtension',
      'arn:aws:lambda:ap-southeast-2:665172237481:layer:AWS-Parameters-and-Secrets-Lambda-Extension-Arm64:11'
    );

    // There are 2 lambdas for this app
    // 1. To sync db with external sources (e.g. metadata in gsheet)
    // 2. To handle API calls (inc graphql endpoint)

    // (1) Lambda that handles updates
    const trackingSheetCredSSM = ssm.StringParameter.fromSecureStringParameterAttributes(
      this,
      'GSheetCredSSM',
      { parameterName: '/umccr/google/drive/lims_service_account_json' }
    );
    const trackingSheetIdSSM = ssm.StringParameter.fromSecureStringParameterAttributes(
      this,
      'TrackingSheetIdSSM',
      { parameterName: '/umccr/google/drive/tracking_sheet_id' }
    );

    const loaderLambda = new lambda.Function(this, 'SyncFunction', {
      description: 'handles loading metadata to the Metadata Manager',
      runtime: lambda.Runtime.NODEJS_18_X,
      code: lambda.Code.fromAsset(path.join(__dirname, '../../../asset/src.zip')),
      handler: 'src/handler/sync.handler',
      architecture: lambda.Architecture.ARM_64,
      timeout: Duration.seconds(300),
      layers: [dependencyLayer, awsSecretLambdaLayerExtension],
      environment: {
        ...edgedbConnectionEnv,
        GDRIVE_SERVICE_ACCOUNT_PARAMETER_NAME: trackingSheetCredSSM.parameterName,
        TRACKING_SHEET_ID_PARAMETER_NAME: trackingSheetIdSSM.parameterName,
      },
      securityGroups: [props.edgedDb.securityGroup, outboundSG],
      vpc: props.network.vpc,
    });
    // Lambda loader need to able to access parameter store that save google credentials
    trackingSheetCredSSM.grantRead(loaderLambda);
    trackingSheetIdSSM.grantRead(loaderLambda);

    // The lambda ideally will be on a scheduled interval
    new events.Rule(this, 'AutoSyncLambdaRule', {
      description: 'this rule is to trigger the metadata load',
      schedule: props.configuration.triggerLoadSchedule,
      targets: [new targets.LambdaFunction(loaderLambda)],
    });

    // (2) Lambda that handles API queries
    const apiLambda = new lambda.Function(this, 'ApiFunction', {
      description: 'handles API query for Metadata Manager in OrcaBus',
      runtime: lambda.Runtime.NODEJS_18_X,
      code: lambda.Code.fromAsset(path.join(__dirname, '../../../asset/src.zip')),
      handler: 'src/handler/server.handler',
      architecture: lambda.Architecture.ARM_64,
      timeout: Duration.minutes(15),
      layers: [dependencyLayer, awsSecretLambdaLayerExtension],
      environment: { ...edgedbConnectionEnv },
      securityGroups: [props.edgedDb.securityGroup, outboundSG],
      vpc: props.network.vpc,
    });

    // Both lambda would need access for edgeDb password secret for the connection
    props.edgedDb.secret.grantRead(apiLambda);
    props.edgedDb.secret.grantRead(loaderLambda);

    // The API lambda will have integration with an API Gateway
    const metadataApiLambdaIntegration = new HttpLambdaIntegration(
      'metadataManagerApiIntegration',
      apiLambda
    );

    if (props.network.apiGatewayHttpApiId) {
      throw new Error('Not yet implemented');

      // Ref: Possible solution is to use HttpRoute, but need to test compatibility
      // https://github.com/aws/aws-cdk/issues/12337#issuecomment-991092668

      // const httpApi = HttpApi.fromHttpApiAttributes(this, 'MetadataManagerOrcabusHttpApi', {
      //   httpApiId: props.network.apiGatewayHttpApiId,
      // });

      // new HttpRoute(this, id, {
      //   httpApi: httpApi,
      //   integration: metadataApiLambdaIntegration,
      //   routeKey: HttpRouteKey.with('/{proxy+}'),
      // });
    } else {
      // const httpApi = new HttpApi(this, 'MetadataManagerHttpApi', {
      //   corsPreflight: {
      //     allowHeaders: ['Authorization'],
      //     allowMethods: [
      //       CorsHttpMethod.GET,
      //       CorsHttpMethod.HEAD,
      //       CorsHttpMethod.OPTIONS,
      //       CorsHttpMethod.POST,
      //     ],
      //     allowOrigins: ['*'], // TODO to get this allowed origins from config constant
      //     maxAge: Duration.days(10),
      //   },
      //   description: 'API for orcabus metadata manager lambda',
      // });
      // httpApi.addRoutes({
      //   integration: metadataApiLambdaIntegration,
      //   path: '/{proxy+}',
      //   methods: [HttpMethod.ANY],
      // });
    }
  }
}
