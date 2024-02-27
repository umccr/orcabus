import { Duration } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as nodejs from 'aws-cdk-lib/aws-lambda-nodejs';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import { DbAuthType, MicroserviceConfig } from '../function/utils';

export type PostgresManagerConfig = {
  masterSecretName: string;
  dbClusterIdentifier: string;
  microserviceDbConfig: MicroserviceConfig;
  clusterResourceIdParameterName: string;
};

export type PostgresManagerStackProps = PostgresManagerConfig & {
  vpc: ec2.IVpc;
  lambdaSecurityGroup: ec2.ISecurityGroup;
};

export class PostgresManager extends Construct {
  constructor(scope: Construct, id: string, props: PostgresManagerStackProps) {
    super(scope, id);

    const { dbClusterIdentifier, microserviceDbConfig } = props;

    const masterSecret = secretsmanager.Secret.fromSecretNameV2(
      this,
      'RdsMasterSecret',
      props.masterSecretName
    );

    const dbClusterResourceId = ssm.StringParameter.valueFromLookup(
      this,
      '/orcabus/db-cluster-resource-id'
    );

    // Let lambda access secret manager via aws managed lambda extension
    // Ref:
    // https://aws.amazon.com/blogs/compute/using-the-aws-parameter-and-secrets-lambda-extension-to-cache-parameters-and-secrets/
    const lambdaLayerGetSecretExtension = lambda.LayerVersion.fromLayerVersionArn(
      this,
      'GetSecretExtensionLayer',
      'arn:aws:lambda:ap-southeast-2:665172237481:layer:AWS-Parameters-and-Secrets-Lambda-Extension-Arm64:11'
    );

    const rdsLambdaProps = {
      timeout: Duration.minutes(5),
      depsLockFilePath: __dirname + '/../yarn.lock',
      handler: 'handler',
      layers: [lambdaLayerGetSecretExtension],
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

    // create new database lambda
    const createPgDb = new nodejs.NodejsFunction(this, 'CreateDbPostgresLambda', {
      ...rdsLambdaProps,
      entry: __dirname + '/../function/create-pg-db.ts',
      functionName: 'orcabus-create-pg-db',
    });
    masterSecret.grantRead(createPgDb);

    // create role which has the rds-iam
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

    // create role with username-password login
    const createRolePgLambda = new nodejs.NodejsFunction(this, 'CreateUserPassPostgresLambda', {
      ...rdsLambdaProps,
      initialPolicy: [
        new iam.PolicyStatement({
          actions: ['secretsmanager:CreateSecret', 'secretsmanager:TagResource'],
          effect: iam.Effect.ALLOW,
          resources: ['arn:aws:secretsmanager:ap-southeast-2:*:secret:*'],
        }),
      ],
      entry: __dirname + '/../function/create-pg-login-role.ts',
      functionName: 'orcabus-create-pg-login-role',
    });
    masterSecret.grantRead(createRolePgLambda);

    // alter db owner to its respective role
    const alterDbPgOwnerLambda = new nodejs.NodejsFunction(this, 'AlterDbOwnerPostgresLambda', {
      ...rdsLambdaProps,
      entry: __dirname + '/../function/alter-pg-db-owner.ts',
      functionName: 'orcabus-alter-pg-db-owner',
    });
    masterSecret.grantRead(alterDbPgOwnerLambda);
  }
}
