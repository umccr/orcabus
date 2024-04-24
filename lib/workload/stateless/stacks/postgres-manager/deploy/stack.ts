import { Duration, RemovalPolicy, Stack, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as nodejs from 'aws-cdk-lib/aws-lambda-nodejs';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { Vpc, VpcLookupOptions, SubnetType, SecurityGroup } from 'aws-cdk-lib/aws-ec2';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as sm from 'aws-cdk-lib/aws-secretsmanager';
import { MicroserviceConfig, DbAuthType } from '../function/type';
import { ProviderFunction } from '../../../../components/provider-function';

export type PostgresManagerStackProps = {
  /**
   * Secret name of the superuser credentials
   */
  masterSecretName: string;
  /**
   * The Db cluster Id
   */
  dbClusterIdentifier: string;
  /**
   * The microservice configuration
   */
  microserviceDbConfig: MicroserviceConfig;
  /**
   * The SSM parameter name that contains the cluster resource id
   */
  clusterResourceIdParameterName: string;
  /**
   * The port of the database
   */
  dbPort: number;
  /**
   * The schedule (in Duration) that will rotate the microservice app secret
   */
  secretRotationSchedule: Duration;
  /**
   * VPC (lookup props) that will be used by resources
   */
  vpcProps: VpcLookupOptions;
  /**
   * Existing security group name to be attached on lambdas
   */
  lambdaSecurityGroupName: string;
};

export class PostgresManagerStack extends Stack {
  // From default: https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_rds.DatabaseSecret.html#excludecharacters
  readonly passExcludedCharacter = '" %+~`#$&()|[]{}:;' + `<>?!'/@"\\")*`;

  constructor(scope: Construct, id: string, props: StackProps & PostgresManagerStackProps) {
    super(scope, id, props);

    const vpc = Vpc.fromLookup(this, 'MainVpc', props.vpcProps);
    const lambdaSG = SecurityGroup.fromLookupByName(
      this,
      'LambdaSecurityGroup',
      props.lambdaSecurityGroupName,
      vpc
    );

    const masterSecret = secretsmanager.Secret.fromSecretNameV2(
      this,
      'RdsMasterSecret',
      props.masterSecretName
    );

    const dbClusterResourceId = ssm.StringParameter.valueForStringParameter(
      this,
      props.clusterResourceIdParameterName
    );

    const dbCluster = rds.DatabaseCluster.fromDatabaseClusterAttributes(this, 'OrcaBusDbCluster', {
      clusterIdentifier: props.dbClusterIdentifier,
      clusterResourceIdentifier: dbClusterResourceId,
      port: props.dbPort,
    });

    const updatePgLambda = new nodejs.NodejsFunction(this, 'UpdatePostgresLambda', {
      depsLockFilePath: __dirname + '/../yarn.lock',
      entry: __dirname + '/../function/index.ts',
      timeout: Duration.minutes(10),
      handler: 'handler',
      runtime: lambda.Runtime.NODEJS_20_X,
      architecture: lambda.Architecture.ARM_64,
      vpc: vpc,
      vpcSubnets: {
        subnetType: SubnetType.PRIVATE_WITH_EGRESS,
      },
      securityGroups: [lambdaSG],
      environment: {
        MICRO_SECRET_MANAGER_TEMPLATE_NAME: PostgresManagerStack.formatDbSecretManagerName(
          '{replace_microservice_name}'
        ),
        RDS_SECRET_MANAGER_NAME: masterSecret.secretName,
        MICROSERVICE_CONFIG: JSON.stringify(props.microserviceDbConfig),
      },
    });
    masterSecret.grantRead(updatePgLambda);

    new ProviderFunction(this, 'UpdatePgProviderFunction', {
      vpc: vpc,
      function: updatePgLambda,
      additionalHash: JSON.stringify(props.microserviceDbConfig),
    });

    // each microservice will have its own role/SM to login

    // the template of the secret where it has common props
    const secretTemplateJson = {
      engine: masterSecret.secretValueFromJson('engine').unsafeUnwrap(),
      host: masterSecret.secretValueFromJson('host').unsafeUnwrap(),
      port: masterSecret.secretValueFromJson('port').unsafeUnwrap(),
    };

    for (const microservice of props.microserviceDbConfig) {
      if (microservice.authType == DbAuthType.RDS_IAM) {
        // create iam-policy that could be assumed when using the rds-iam

        const iamPolicy = new iam.ManagedPolicy(this, `${microservice.name}RdsIamPolicy`, {
          managedPolicyName: PostgresManagerStack.formatRdsPolicyName(microservice.name),
        });
        dbCluster.grantConnect(iamPolicy, microservice.name);
      } else if (microservice.authType == DbAuthType.USERNAME_PASSWORD) {
        // create secret manager (+ rotator) for specific µ-app

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

        new sm.SecretRotation(this, `${microservice.name}DbSecretRotation`, {
          application: sm.SecretRotationApplication.POSTGRES_ROTATION_SINGLE_USER,
          excludeCharacters: this.passExcludedCharacter,
          secret: microSM,
          target: dbCluster,
          automaticallyAfter: props.secretRotationSchedule,
          securityGroup: lambdaSG,
          vpc: vpc,
          vpcSubnets: {
            subnetType: SubnetType.PRIVATE_WITH_EGRESS,
          },
        });

        // the pg lambda need to access the SM to set the role password
        microSM.grantRead(updatePgLambda);
      }
    }
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
