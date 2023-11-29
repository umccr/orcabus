import {
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
import { EdgeDbConfigurationProps } from '../edge-db/edge-db-construct';

export interface appProps {
  edgedDb: {
    edgeDbConfiguration: EdgeDbConfigurationProps;
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

    // edgeDb environment to make connection the edgeDb instance
    const edgeDbConnectionEnv = {
      ...props.edgedDb.edgeDbConfiguration,
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

    // There are 2 lambdas for this app
    // 1. To handle API calls (inc graphql endpoint)
    // 2. To sync db with external sources (e.g. metadata in gsheet)

    // (1) Lambda that handles API queries
    const apiLambda = new lambda.DockerImageFunction(this, 'APILambda', {
      description: 'handles API query for Metadata Manager in OrcaBus',
      code: lambda.DockerImageCode.fromImageAsset(path.join(__dirname, '../../../'), {
        file: 'deploy/construct/app/Dockerfile',
        exclude: ['deploy/cdk.out', 'deploy/asset', '.yarn'],
        cmd: ['src/handler/server.handler'],
        buildArgs: {
          AWS_ACCESS_KEY_ID: process.env.AWS_ACCESS_KEY_ID ?? '',
          AWS_SECRET_ACCESS_KEY: process.env.AWS_SECRET_ACCESS_KEY ?? '',
          AWS_SESSION_TOKEN: process.env.AWS_SESSION_TOKEN ?? '',
        },
      }),
      architecture: lambda.Architecture.ARM_64,
      timeout: Duration.minutes(15),
      environment: { ...edgeDbConnectionEnv },
      securityGroups: [props.edgedDb.securityGroup, outboundSG],
      vpc: props.network.vpc,
    });

    // (2) Lambda that handles updates
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

    const loaderLambda = new lambda.DockerImageFunction(this, 'loaderLambda', {
      description: 'handles loading metadata to the Metadata Manager',
      code: lambda.DockerImageCode.fromImageAsset(path.join(__dirname, '../../../'), {
        file: 'deploy/construct/app/Dockerfile',
        exclude: ['deploy/cdk.out', 'deploy/asset', '.yarn'],
        cmd: ['src/handler/sync.handler'],
        buildArgs: {
          AWS_ACCESS_KEY_ID: process.env.AWS_ACCESS_KEY_ID ?? '',
          AWS_SECRET_ACCESS_KEY: process.env.AWS_SECRET_ACCESS_KEY ?? '',
          AWS_SESSION_TOKEN: process.env.AWS_SESSION_TOKEN ?? '',
        },
      }),
      architecture: lambda.Architecture.ARM_64,
      timeout: Duration.seconds(300),
      environment: {
        ...edgeDbConnectionEnv,
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
      const httpApi = new HttpApi(this, 'MetadataManagerHttpApi', {
        corsPreflight: {
          allowHeaders: ['Authorization'],
          allowMethods: [
            CorsHttpMethod.GET,
            CorsHttpMethod.HEAD,
            CorsHttpMethod.OPTIONS,
            CorsHttpMethod.POST,
          ],
          allowOrigins: ['*'], // TODO to get this allowed origins from config constant
          maxAge: Duration.days(10),
        },
        description: 'API for orcabus metadata manager lambda',
      });
      httpApi.addRoutes({
        integration: metadataApiLambdaIntegration,
        path: '/{proxy+}',
        methods: [HttpMethod.ANY],
      });
    }
  }
}
