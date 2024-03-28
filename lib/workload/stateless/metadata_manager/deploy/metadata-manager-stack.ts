import path from 'path';
import * as cdk from 'aws-cdk-lib';
import { aws_lambda, Stack } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { ISecurityGroup, IVpc } from 'aws-cdk-lib/aws-ec2';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as sm from 'aws-cdk-lib/aws-secretsmanager';
import * as events from 'aws-cdk-lib/aws-events';

// import { IEventBus } from 'aws-cdk-lib/aws-events';
import { PythonFunction, PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
// import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';
// import { HttpMethod, HttpRoute, HttpRouteKey, HttpStage } from 'aws-cdk-lib/aws-apigatewayv2';
// import { ManagedPolicy, Role, ServicePrincipal } from 'aws-cdk-lib/aws-iam';
// import { SRMApiGatewayConstruct } from './construct/component';
import { Architecture } from 'aws-cdk-lib/aws-lambda';

// Follow by naming convention. See https://github.com/umccr/orcabus/pull/149
const MM_RDS_CRED_SECRET_NAME = 'orcabus/metadata_manager/rdsLoginCredential'; // pragma: allowlist secret

const GDRIVE_CRED_PARAM_NAME = '/umccr/google/drive/lims_service_account_json';
const GDRIVE_SHEET_ID_PARAM_NAME = '/umccr/google/drive/tracking_sheet_id';

export type MetadataManagerConfig = {
  syncInterval?: events.Schedule;
};

export interface MetadataManagerProps {
  lambdaSecurityGroups: ISecurityGroup;
  vpc: IVpc;
  // mainBus: IEventBus;
}

export class MetadataManagerStack extends Stack {
  constructor(
    scope: Construct,
    id: string,
    props: cdk.StackProps & MetadataManagerProps & MetadataManagerConfig
  ) {
    super(scope, id);

    // lookup the secret manager resource so we could give lambda permissions
    const dbSecret = sm.Secret.fromSecretNameV2(
      this,
      'DbSecretConnection',
      MM_RDS_CRED_SECRET_NAME
    );

    // despite of multiple lambda, all of them will share the same dependencies, as only the
    // entrypoints are different
    const baseLayer = new PythonLayerVersion(this, 'DependenciesLayer', {
      entry: path.join(__dirname, '../deps'),
      compatibleRuntimes: [aws_lambda.Runtime.PYTHON_3_12],
      compatibleArchitectures: [Architecture.ARM_64],
    });

    const sharedLambdaEnv = {
      DJANGO_SETTINGS_MODULE: 'app.settings.aws',
      RDS_CRED_SECRET_NAME: MM_RDS_CRED_SECRET_NAME,
    };

    const basicLambdaConfig = {
      entry: path.join(__dirname, '../'),
      runtime: aws_lambda.Runtime.PYTHON_3_12,
      layers: [baseLayer],
      environment: sharedLambdaEnv,
      securityGroups: [props.lambdaSecurityGroups],
      vpc: props.vpc,
      vpcSubnets: { subnets: props.vpc.privateSubnets },
      architecture: Architecture.ARM_64,
    };

    // There are 2 lambdas for this app
    // 1. To handle API calls from API-GW
    // 2. To do migrations
    // 3. To sync db with external sources (e.g. metadata in gsheet)

    // (1) Lambda that handles API queries
    const apiHandlerLambda = new PythonFunction(this, 'APILambda', {
      ...basicLambdaConfig,
      index: 'api.py',
      handler: 'handler',
      timeout: cdk.Duration.seconds(28),
    });
    dbSecret.grantRead(apiHandlerLambda);

    // (2) migrations lambda
    const migrationsLambda = new PythonFunction(this, 'MigrationLambda', {
      ...basicLambdaConfig,
      index: 'migrate.py',
      handler: 'handler',
      timeout: cdk.Duration.minutes(5),
    });
    dbSecret.grantRead(migrationsLambda);

    // (3) sync db with gsheet

    const syncGSheetLambda = new PythonFunction(this, 'SyncLambda', {
      ...basicLambdaConfig,
      index: 'proc/lambdas/sync_tracking_sheet.py',
      handler: 'handler',
      timeout: cdk.Duration.minutes(5),
    });
    dbSecret.grantRead(migrationsLambda);

    // the sync-db lambda would need some cred to access GDrive and these are stored in SSM
    const trackingSheetCredSSM = ssm.StringParameter.fromSecureStringParameterAttributes(
      this,
      'GSheetCredSSM',
      { parameterName: GDRIVE_CRED_PARAM_NAME }
    );
    const trackingSheetIdSSM = ssm.StringParameter.fromSecureStringParameterAttributes(
      this,
      'TrackingSheetIdSSM',
      { parameterName: GDRIVE_SHEET_ID_PARAM_NAME }
    );
    trackingSheetCredSSM.grantRead(syncGSheetLambda);
    trackingSheetIdSSM.grantRead(syncGSheetLambda);
  }
}
