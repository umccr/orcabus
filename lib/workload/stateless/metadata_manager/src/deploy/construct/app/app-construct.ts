import {
  RemovalPolicy,
  aws_ec2 as ec2,
  aws_secretsmanager as secretsmanager,
  aws_lambda as lambda,
  // aws_ssm as ssm,
  Duration,
} from 'aws-cdk-lib';
import * as path from 'path';
import { Construct } from 'constructs';
import { ISecurityGroup } from 'aws-cdk-lib/aws-ec2';
export interface appProps {
  edgedDb: {
    databaseName: string;
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
    // 2. To db with externalow  sources
    // 3. To do some admin stuff at edgeDb instance (edgeDb mgiration)

    // Lambda would need to access Secret Manager to retrieve edgedb password
    // thus need an outbound traffic from SG to do so
    const outboundSG = new ec2.SecurityGroup(this, 'MembershipSecurityGroup', {
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
    // but AWS have an extension for this by importing an existing AWS layer
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
      handler: 'src/handler/migrate.handler',
      architecture: lambda.Architecture.ARM_64,
      timeout: Duration.seconds(30),
      layers: [dependencyLayer, awsSecretLambdaLayerExtension],
      environment: {
        EDGEDB_DATABASE: props.edgedDb.databaseName,
        EDGEDB_DSN: props.edgedDb.dsnNoPassword,
        EDGEDB_SECRET_NAME: props.edgedDb.secret.secretName,
      },
      securityGroups: [props.edgedDb.securityGroup, outboundSG],
      vpc: props.network.vpc,
    });

    const migrationLambda = new lambda.Function(this, 'MigrationFunction', {
      description: 'handles migration for Metadata Manager in OrcaBus',
      runtime: lambda.Runtime.NODEJS_18_X,
      code: lambda.Code.fromAsset(path.join(__dirname, '../../../asset/src.zip')),
      handler: 'src/handler/migrate.handler',
      architecture: lambda.Architecture.ARM_64,
      timeout: Duration.minutes(5),
      layers: [dependencyLayer, awsSecretLambdaLayerExtension],
      environment: {
        EDGEDB_DATABASE: props.edgedDb.databaseName,
        EDGEDB_DSN: props.edgedDb.dsnNoPassword,
        EDGEDB_SECRET_NAME: props.edgedDb.secret.secretName,
      },
      securityGroups: [props.edgedDb.securityGroup, outboundSG],
      vpc: props.network.vpc,
    });

    // lambda would need access for edgeDb password secret for the connection
    props.edgedDb.secret.grantRead(apiLambda);
    props.edgedDb.secret.grantRead(migrationLambda);

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
    //   environment: {
    //     EDGEDB_DATABASE: props.edgedDb.databaseName,
    //     EDGEDB_DSN: props.edgedDb.dsnNoPassword,
    //     EDGEDB_SECRET_NAME: props.edgedDb.secret.secretName,
    //   },
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
  }
}
