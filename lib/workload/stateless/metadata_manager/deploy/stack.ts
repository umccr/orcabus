import path from 'path';
import { Construct } from 'constructs';
import { Stack, StackProps } from 'aws-cdk-lib';
import { ISecurityGroup, IVpc } from 'aws-cdk-lib/aws-ec2';
import { Secret } from 'aws-cdk-lib/aws-secretsmanager';
import { Schedule } from 'aws-cdk-lib/aws-events';
import { Code, Runtime, Architecture, LayerVersion } from 'aws-cdk-lib/aws-lambda';

// import custom constructs
import { LambdaSyncGsheetConstruct } from './construct/lambda-sync-gsheet';
import { LambdaMigrationConstruct } from './construct/lambda-migration';
import { LambdaAPIConstruct } from './construct/lambda-api';
import { ApiGatewayConstruct } from './construct/api-gw';

/**
 * this config should be configured at the top (root) cdk app
 */
export type MetadataManagerConfig = {
  /**
   * the interval where the lambda conduct the sync from the single source of truth data
   */
  syncInterval?: Schedule;
};

/**
 * the props expected when the (metadata-manager) stack is constructed
 */
export type MetadataManagerProps = MetadataManagerConfig & {
  /**
   * the special security group that will be attached to lambdas (e.g. SG allow to access db cluster)
   */
  lambdaSecurityGroups: ISecurityGroup;
  /**
   * vpc where the lambdas will deploy
   */
  vpc: IVpc;
};

export class MetadataManagerStack extends Stack {
  // Follow by naming convention. See https://github.com/umccr/orcabus/pull/149
  private readonly MM_RDS_CRED_SECRET_NAME = 'orcabus/metadata_manager/rdsLoginCredential'; // pragma: allowlist secret

  constructor(scope: Construct, id: string, props: StackProps & MetadataManagerProps) {
    super(scope, id);

    // lookup the secret manager resource so we could give lambda permissions to read it
    const dbSecret = Secret.fromSecretNameV2(
      this,
      'DbSecretConnection',
      this.MM_RDS_CRED_SECRET_NAME
    );

    // despite of multiple lambda all of them will share the same dependencies
    const dependencySlimLayer = new LayerVersion(this, 'DependenciesLayer', {
      code: Code.fromDockerBuild(__dirname + '/../', {
        file: 'deps/requirements-slim.Dockerfile',
        imagePath: 'home/output',
      }),
      compatibleArchitectures: [Architecture.ARM_64],
      compatibleRuntimes: [Runtime.PYTHON_3_12],
    });

    const basicLambdaConfig = {
      entry: path.join(__dirname, '../'),
      runtime: Runtime.PYTHON_3_12,
      layers: [dependencySlimLayer],
      environment: {
        DJANGO_SETTINGS_MODULE: 'app.settings.aws',
        RDS_CRED_SECRET_NAME: this.MM_RDS_CRED_SECRET_NAME,
      },
      securityGroups: [props.lambdaSecurityGroups],
      vpc: props.vpc,
      vpcSubnets: { subnets: props.vpc.privateSubnets },
      architecture: Architecture.ARM_64,
    };

    // There are 2 lambdas for this app
    // 1. To handle API calls from API-GW
    // 2. To do migrations
    // 3. To sync db with external sources (e.g. metadata in gsheet)

    // (1)
    const apiGW = new ApiGatewayConstruct(this, 'APIGW').httpApi;
    new LambdaAPIConstruct(this, 'APILambda', {
      basicLambdaConfig: basicLambdaConfig,
      dbConnectionSecret: dbSecret,
      apiGW: apiGW,
    });

    // (2)
    new LambdaMigrationConstruct(this, 'MigrationLambda', {
      basicLambdaConfig: basicLambdaConfig,
      dbConnectionSecret: dbSecret,
    });

    // (3)
    new LambdaSyncGsheetConstruct(this, 'SyncGsheetLambda', {
      basicLambdaConfig: basicLambdaConfig,
      dbConnectionSecret: dbSecret,
    });
  }
}
