import { Duration, RemovalPolicy, SecretValue, Stack, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as nodejs from 'aws-cdk-lib/aws-lambda-nodejs';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as sm from 'aws-cdk-lib/aws-secretsmanager';
import { MicroserviceConfig, DbAuthType } from '../function/type';
import package_json from '../package.json';

export type PostgresManagerConfig = {
  masterSecretName: string;
  dbClusterIdentifier: string;
  microserviceDbConfig: MicroserviceConfig;
  clusterResourceIdParameterName: string;
  dbPort: number;
  /**
   * The schedule (in Duration) that will rotate the microservice app secret
   */
  secretRotationSchedule: Duration;
};

export type PostgresManagerProps = PostgresManagerConfig & {
  vpc: ec2.IVpc;
  lambdaSecurityGroup: ec2.ISecurityGroup;
};

export class PostgresManagerStack extends Stack {
  // From default: https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_rds.DatabaseSecret.html#excludecharacters
  readonly passExcludedCharacter = '" %+~`#$&()|[]{}:;' + `<>?!'/@"\\")*`;

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

    const dbCluster = rds.DatabaseCluster.fromDatabaseClusterAttributes(this, 'OrcabusDbCluster', {
      clusterIdentifier: dbClusterIdentifier,
      clusterResourceIdentifier: dbClusterResourceId,
      port: props.dbPort,
    });

    const dependencyLayer = new lambda.LayerVersion(this, 'DependenciesLayer', {
      code: lambda.Code.fromDockerBuild(__dirname + '/../', {
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
          managedPolicyName: PostgresManagerStack.formatRdsPolicyName(microservice.name),
        });
        dbCluster.grantConnect(iamPolicy, microservice.name);
      }
    }

    // 3. lambda responsible on role creation with username-password auth

    // the template of the secret where it has common props
    const secretTemplateJson = {
      engine: masterSecret.secretValueFromJson('engine').unsafeUnwrap(),
      host: masterSecret.secretValueFromJson('host').unsafeUnwrap(),
      port: masterSecret.secretValueFromJson('port').unsafeUnwrap(),
    };

    const secretManagerArray = [];
    for (const microservice of microserviceDbConfig) {
      if (microservice.authType == DbAuthType.USERNAME_PASSWORD) {
        // create secret manager for specific µ-app
        const microSM = new sm.Secret(this, `${microservice.name}UserPassCred`, {
          description: `orcabus microservice secret for '${microservice.name}'`,
          generateSecretString: {
            excludeCharacters: this.passExcludedCharacter,
            generateStringKey: 'password',
            secretStringTemplate: JSON.stringify({
              ...secretTemplateJson,
              dbname: microservice.name,
              username: microservice.name,
            }),
          },
          removalPolicy: RemovalPolicy.DESTROY,
          secretName: PostgresManagerStack.formatDbSecretManagerName(microservice.name),
        });

        // rotating these SM
        new sm.SecretRotation(this, `${microservice.name}DbSecretRotation`, {
          application: sm.SecretRotationApplication.POSTGRES_ROTATION_SINGLE_USER,
          excludeCharacters: this.passExcludedCharacter,
          secret: microSM,
          target: dbCluster,
          automaticallyAfter: props.secretRotationSchedule,
          securityGroup: props.lambdaSecurityGroup,
          vpc: props.vpc,
          vpcSubnets: {
            subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
          },
        });

        // pushing to an array so it can be referred later
        secretManagerArray.push(microSM);
      }
    }

    const createRolePgLambda = new nodejs.NodejsFunction(this, 'CreateUserPassPostgresLambda', {
      ...rdsLambdaProps,
      entry: __dirname + '/../function/create-pg-login-role.ts',
      functionName: 'orcabus-create-pg-login-role',
    });
    createRolePgLambda.addEnvironment(
      'MICRO_SECRET_MANAGER_TEMPLATE_NAME',
      PostgresManagerStack.formatDbSecretManagerName('{replace_microservice_name}')
    );

    // grant lambda master secret
    masterSecret.grantRead(createRolePgLambda);

    // grant to read all microservice secret name
    for (const secret of secretManagerArray) {
      secret.grantRead(createRolePgLambda);
    }

    // 4. lambda responsible on alter db owner
    const alterDbPgOwnerLambda = new nodejs.NodejsFunction(this, 'AlterDbOwnerPostgresLambda', {
      ...rdsLambdaProps,
      entry: __dirname + '/../function/alter-pg-db-owner.ts',
      functionName: 'orcabus-alter-pg-db-owner',
    });
    masterSecret.grantRead(alterDbPgOwnerLambda);
  }

  /**
   * Format the name of the managed policy which is created for a microservice using RDS credentials.
   * @param microserviceName the name of the microservice
   */
  static formatRdsPolicyName(microserviceName: string) {
    return `orcabus-rds-connect-${microserviceName}`;
  }

  /**
   * Format the name of the secret manager used for microservice connection string
   * @param microserviceName the name of the microservice
   */
  static formatDbSecretManagerName(microserviceName: string) {
    return `orcabus/${microserviceName}/rds-login-credential`;
  }
}
