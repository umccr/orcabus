import { Duration, Stack, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as nodejs from 'aws-cdk-lib/aws-lambda-nodejs';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { MicroserviceConfig, DbAuthType } from '../function/type';
import package_json from '../package.json';

export type PostgresManagerConfig = {
  masterSecretName: string;
  dbClusterIdentifier: string;
  microserviceDbConfig: MicroserviceConfig;
  clusterResourceIdParameterName: string;
};

export type PostgresManagerProps = PostgresManagerConfig & {
  vpc: ec2.IVpc;
  lambdaSecurityGroup: ec2.ISecurityGroup;
};

export class PostgresManagerStack extends Stack {
  constructor(scope: Construct, id: string, props: StackProps & PostgresManagerProps) {
    super(scope, id);

    const { dbClusterIdentifier, microserviceDbConfig } = props;

    const masterSecret = secretsmanager.Secret.fromSecretNameV2(
      this,
      'RdsMasterSecret',
      props.masterSecretName
    );

    const dbClusterResourceId = ssm.StringParameter.valueForStringParameter(
      this,
      props.clusterResourceIdParameterName
    );

    const dependencyLayer = new lambda.LayerVersion(this, 'DependenciesLayer', {
      code: lambda.Code.fromDockerBuild(__dirname + '/../', {
        cacheDisabled: true,
        file: 'deploy/construct/layer/node_module.Dockerfile',
        imagePath: 'home/node/app/output',
      }),
      compatibleArchitectures: [lambda.Architecture.ARM_64],
      compatibleRuntimes: [lambda.Runtime.NODEJS_20_X],
    });

    const runtimeDependencies = Object.keys(package_json.dependencies);
    const rdsLambdaProps: nodejs.NodejsFunctionProps = {
      layers: [dependencyLayer],
      bundling: { externalModules: runtimeDependencies },
      timeout: Duration.minutes(5),
      handler: 'handler',
      runtime: lambda.Runtime.NODEJS_20_X,
      architecture: lambda.Architecture.ARM_64,
      environment: {
        RDS_SECRET_MANAGER_NAME: masterSecret.secretName,
        MICROSERVICE_CONFIG: JSON.stringify(props.microserviceDbConfig),
      },
      vpc: props.vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
      },
      securityGroups: [props.lambdaSecurityGroup],
    };

    // 1. lambda responsible on db creation
    const createPgDb = new nodejs.NodejsFunction(this, 'CreateDbPostgresLambda', {
      ...rdsLambdaProps,
      entry: __dirname + '/../function/create-pg-db.ts',
      functionName: 'orcabus-create-pg-db',
    });
    masterSecret.grantRead(createPgDb);

    // 2. lambda responsible on role creation with rds_iam
    const initiatePgRdsIam = new nodejs.NodejsFunction(this, 'CreateIamUserPostgresLambda', {
      ...rdsLambdaProps,
      entry: __dirname + '/../function/create-pg-iam-role.ts',
      functionName: 'orcabus-create-pg-iam-role',
    });
    masterSecret.grantRead(initiatePgRdsIam);

    // create iam-policy that could be assumed when using the rds-iam
    for (const microservice of microserviceDbConfig) {
      if (microservice.authType == DbAuthType.RDS_IAM) {
        const iamPolicy = new iam.ManagedPolicy(this, `${microservice.name}RdsIamPolicy`, {
          managedPolicyName: `orcabus-rds-connect-${microservice.name}`,
        });

        const dbCluster = rds.DatabaseCluster.fromDatabaseClusterAttributes(
          this,
          'OrcabusDbCluster',
          {
            clusterIdentifier: dbClusterIdentifier,
            clusterResourceIdentifier: dbClusterResourceId,
          }
        );

        dbCluster.grantConnect(iamPolicy, microservice.name);
      }
    }

    // 3. lambda responsible on role creation with username-password auth
    const createRolePgLambda = new nodejs.NodejsFunction(this, 'CreateUserPassPostgresLambda', {
      ...rdsLambdaProps,
      initialPolicy: [
        new iam.PolicyStatement({
          actions: ['secretsmanager:CreateSecret', 'secretsmanager:TagResource'],
          effect: iam.Effect.ALLOW,
          resources: [`arn:aws:secretsmanager:ap-southeast-2:*:secret:*`],
        }),
        new iam.PolicyStatement({
          actions: ['secretsmanager:GetRandomPassword'],
          effect: iam.Effect.ALLOW,
          resources: ['*'],
        }),
      ],
      entry: __dirname + '/../function/create-pg-login-role.ts',
      functionName: 'orcabus-create-pg-login-role',
    });
    masterSecret.grantRead(createRolePgLambda);

    // 4. lambda responsible on alter db owner
    const alterDbPgOwnerLambda = new nodejs.NodejsFunction(this, 'AlterDbOwnerPostgresLambda', {
      ...rdsLambdaProps,
      entry: __dirname + '/../function/alter-pg-db-owner.ts',
      functionName: 'orcabus-alter-pg-db-owner',
    });
    masterSecret.grantRead(alterDbPgOwnerLambda);
  }
}
