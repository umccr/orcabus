import path from 'path';
import { Construct } from 'constructs';
import { Stack, StackProps } from 'aws-cdk-lib';
import { ISecurityGroup, IVpc } from 'aws-cdk-lib/aws-ec2';
import { Secret } from 'aws-cdk-lib/aws-secretsmanager';
import { Schedule } from 'aws-cdk-lib/aws-events';
import { Code, Runtime, Architecture, LayerVersion } from 'aws-cdk-lib/aws-lambda';

// import constructs
import { SyncGsheetLambdaConstruct } from './construct/sync-gsheet-lambda-construct/sync-gsheet-lambda-construct';
import { MigrationLambdaConstruct } from './construct/migration-handler-lambda-construct/migration-handler-lambda-construct';
import { APILambdaConstruct } from './construct/api-handler-lambda-construct/api-handler-lambda-construct';
import { ApiGatewayConstruct } from './construct/api-gw-construct/api-gw-construct';

export type MetadataManagerConfig = {
  syncInterval?: Schedule;
};

export interface MetadataManagerProps {
  lambdaSecurityGroups: ISecurityGroup;
  vpc: IVpc;
}

export class MetadataManagerStack extends Stack {
  // Follow by naming convention. See https://github.com/umccr/orcabus/pull/149
  private readonly MM_RDS_CRED_SECRET_NAME = 'orcabus/metadata_manager/rdsLoginCredential'; // pragma: allowlist secret

  constructor(
    scope: Construct,
    id: string,
    props: StackProps & MetadataManagerProps & MetadataManagerConfig
  ) {
    super(scope, id);

    // lookup the secret manager resource so we could give lambda permissions
    const dbSecret = Secret.fromSecretNameV2(
      this,
      'DbSecretConnection',
      this.MM_RDS_CRED_SECRET_NAME
    );

    // despite of multiple lambda, all of them will share the same dependencies, as only the
    // entrypoints are different
    const dependencySlimLayer = new LayerVersion(this, 'DependenciesLayer', {
      code: Code.fromDockerBuild(__dirname + '/../', {
        file: 'deps/requirements-slim.Dockerfile',
        imagePath: 'home/output',
      }),
      compatibleArchitectures: [Architecture.ARM_64],
      compatibleRuntimes: [Runtime.PYTHON_3_12],
    });

    const sharedLambdaEnv = {
      DJANGO_SETTINGS_MODULE: 'app.settings.aws',
      RDS_CRED_SECRET_NAME: this.MM_RDS_CRED_SECRET_NAME,
    };

    const basicLambdaConfig = {
      entry: path.join(__dirname, '../'),
      runtime: Runtime.PYTHON_3_12,
      layers: [dependencySlimLayer],
      environment: sharedLambdaEnv,
      securityGroups: [props.lambdaSecurityGroups],
      vpc: props.vpc,
      vpcSubnets: { subnets: props.vpc.privateSubnets },
      architecture: Architecture.ARM_64,
    };

    const apiGW = new ApiGatewayConstruct(this, 'APIGW').httpApi;

    // There are 2 lambdas for this app
    // 1. To handle API calls from API-GW
    // 2. To do migrations
    // 3. To sync db with external sources (e.g. metadata in gsheet)

    // (1)
    new APILambdaConstruct(this, 'APILambda', {
      basicLambdaConfig: basicLambdaConfig,
      dbConnectionSecret: dbSecret,
      apiGW: apiGW,
    });

    // (2)
    new MigrationLambdaConstruct(this, 'MigrationLambda', {
      basicLambdaConfig: basicLambdaConfig,
      dbConnectionSecret: dbSecret,
    });

    // (3)
    new SyncGsheetLambdaConstruct(this, 'SyncGsheetLambda', {
      basicLambdaConfig: basicLambdaConfig,
      dbConnectionSecret: dbSecret,
    });
  }
}
