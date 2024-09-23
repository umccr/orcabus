import path from 'path';
import { Construct } from 'constructs';
import { Stack, StackProps } from 'aws-cdk-lib';
import { Vpc, VpcLookupOptions, SecurityGroup } from 'aws-cdk-lib/aws-ec2';
import { Secret } from 'aws-cdk-lib/aws-secretsmanager';
import { Code, Runtime, Architecture, LayerVersion } from 'aws-cdk-lib/aws-lambda';

// import custom constructs
import { LambdaSyncGsheetConstruct } from './construct/lambda-sync-gsheet';
import { LambdaMigrationConstruct } from './construct/lambda-migration';
import { LambdaAPIConstruct } from './construct/lambda-api';
import { ApiGatewayConstructProps } from '../../../../components/api-gateway';
import { PostgresManagerStack } from '../../../../stateful/stacks/postgres-manager/deploy/stack';
import { LambdaLoadCustomCSVConstruct } from './construct/lambda-load-custom-csv';

export type MetadataManagerStackProps = {
  /**
   * VPC (lookup props) that will be used by resources
   */
  vpcProps: VpcLookupOptions;
  /**
   * Existing security group name to be attached on lambdas
   */
  lambdaSecurityGroupName: string;
  /**
   * A boolean to tell whether the sync lambda should run daily
   */
  isDailySync: boolean;
  /**
   * API Gateway props
   */
  apiGatewayCognitoProps: ApiGatewayConstructProps;
  /**
   * API Gateway props
   */
  eventBusName: string;
};

export class MetadataManagerStack extends Stack {
  private readonly MM_RDS_CRED_SECRET_NAME =
    PostgresManagerStack.formatDbSecretManagerName('metadata_manager');

  constructor(scope: Construct, id: string, props: StackProps & MetadataManagerStackProps) {
    super(scope, id, props);

    const vpc = Vpc.fromLookup(this, 'MainVpc', props.vpcProps);
    const lambdaSG = SecurityGroup.fromLookupByName(
      this,
      'LambdaSecurityGroup',
      props.lambdaSecurityGroupName,
      vpc
    );

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
      securityGroups: [lambdaSG],
      vpc: vpc,
      vpcSubnets: { subnets: vpc.privateSubnets },
      architecture: Architecture.ARM_64,
      memorySize: 1024,
    };

    // There are 3 lambdas for this app
    // 1. To handle API calls
    // 2. To do migrations
    // 3. To sync db with external sources (e.g. metadata in gsheet)
    // 4. To load-db from external csv presigned url file

    // (1)
    new LambdaAPIConstruct(this, 'APILambda', {
      basicLambdaConfig: basicLambdaConfig,
      dbConnectionSecret: dbSecret,
      apiGatewayConstructProps: props.apiGatewayCognitoProps,
    });

    // (2)
    new LambdaMigrationConstruct(this, 'MigrationLambda', {
      basicLambdaConfig: basicLambdaConfig,
      dbConnectionSecret: dbSecret,
      vpc: vpc,
    });

    // (3)
    new LambdaSyncGsheetConstruct(this, 'SyncGsheetLambda', {
      basicLambdaConfig: basicLambdaConfig,
      dbConnectionSecret: dbSecret,
      isDailySync: props.isDailySync,
      eventBusName: props.eventBusName,
    });

    // (4)
    new LambdaLoadCustomCSVConstruct(this, 'CustomCsvLoaderLambda', {
      basicLambdaConfig: basicLambdaConfig,
      dbConnectionSecret: dbSecret,
      eventBusName: props.eventBusName,
    });
  }
}
