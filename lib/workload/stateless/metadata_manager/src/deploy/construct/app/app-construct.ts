import {
  RemovalPolicy,
  aws_ec2 as ec2,
  aws_secretsmanager as secretsmanager,
  aws_lambda as lambda,
  Duration,
} from 'aws-cdk-lib';
import * as path from 'path';
import { Construct } from 'constructs';
import { ISecurityGroup } from 'aws-cdk-lib/aws-ec2';
import { HttpLambdaIntegration } from '@aws-cdk/aws-apigatewayv2-integrations-alpha';
import { CorsHttpMethod, HttpApi, HttpMethod, HttpStage } from '@aws-cdk/aws-apigatewayv2-alpha';

export interface appProps {
  edgedDb: {
    dsnNoPassword: string;
    secret: secretsmanager.ISecret;
    securityGroup: ISecurityGroup;
  };
  network: {
    vpc: ec2.IVpc;
  };
}

/**
 * A construct wrapping an installation of EdgeDb as a service (assuming
 * an existing RDS postgres).
 */
export class AppConstruct extends Construct {
  constructor(scope: Construct, id: string, props: appProps) {
    super(scope, id);

    // There are 3 lambdas for this app
    // 1. To handle API calls (inc graphql endpoint)
    // 2. To sync db with external sources (e.g. sync metadata with gsheet)

    // edgedb env
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

    // the layer for all content of code including node_modules
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

    const apiLambda = new lambda.Function(this, 'ApiFunction', {
      description: 'handles API query for Metadata Manager in OrcaBus',
      runtime: lambda.Runtime.NODEJS_18_X,
      code: lambda.Code.fromAsset(path.join(__dirname, '../../../asset/src.zip')),
      handler: 'src/handler/server.handler',
      architecture: lambda.Architecture.ARM_64,
      timeout: Duration.seconds(30),
      layers: [dependencyLayer, awsSecretLambdaLayerExtension],
      environment: { ...edgedbConnectionEnv },
      securityGroups: [props.edgedDb.securityGroup, outboundSG],
      vpc: props.network.vpc,
    });
    // lambda would need access for edgeDb password secret for the connection
    props.edgedDb.secret.grantRead(apiLambda);

    const apiLambdaIntegration = new HttpLambdaIntegration(
      'metadataManagerApiIntegration',
      apiLambda
    );

    // // The app need access to gsheet which the secret is stored in the ssm parameter
    // // granting access to the secret here
    // const loaderLambda = new lambda.Function(this, 'SyncFunction', {
    //   description: 'handles API query for Metadata Manager in OrcaBus',
    //   runtime: lambda.Runtime.NODEJS_18_X,
    //   code: lambda.Code.fromAsset(path.join(__dirname, '../../../asset/src.zip')),
    //   handler: 'src/handler/sync.handler',
    //   architecture: lambda.Architecture.ARM_64,
    //   timeout: Duration.seconds(30),
    //   layers: [dependencyLayer, awsSecretLambdaLayerExtension],
    //   environment: { ...edgedbConnectionEnv },
    //   securityGroups: [props.edgedDb.securityGroup, outboundSG],
    //   vpc: props.network.vpc,
    // });

    // // TODO Possible use lambda layer that query ssm from the Layer's API
    // const trackingSheetCredSSM = ssm.StringParameter.fromStringParameterName(
    //   this,
    //   'GSheetCredSSM',
    //   '/umccr/google/drive/lims_service_account_json'
    // );
    // const trackingSheetIdSSM = ssm.StringParameter.fromStringParameterName(
    //   this,
    //   'TrackingSheetIdSSM',
    //   '/umccr/google/drive/tracking_sheet_id'
    // );
    // trackingSheetCredSSM.grantRead(loaderLambda);
    // trackingSheetIdSSM.grantRead(loaderLambda);

    const httpApi = new HttpApi(this, 'MetadataManagerOrcabusHttpApi', {
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
      integration: apiLambdaIntegration,
      path: '/{proxy+}',
      methods: [HttpMethod.ANY],
    });
  }
}
