import { Construct } from 'constructs';
import { IStringParameter } from 'aws-cdk-lib/aws-ssm';
import { aws_lambda, aws_ssm, Duration, Stack, StackProps } from 'aws-cdk-lib';
import { Secret } from 'aws-cdk-lib/aws-secretsmanager';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import path from 'path';
import { Architecture } from 'aws-cdk-lib/aws-lambda';
import { Role, ServicePrincipal } from 'aws-cdk-lib/aws-iam';
import { IUserPool, UserPool } from 'aws-cdk-lib/aws-cognito';
import { LogGroup } from 'aws-cdk-lib/aws-logs';
import { IVpc, Vpc } from 'aws-cdk-lib/aws-ec2';

export interface TokenServiceProps {
  serviceUserSecretName: string;
  jwtSecretName: string;
  vpcProps: object;
}

export class TokenServiceStack extends Stack {
  private readonly props: TokenServiceProps;
  private readonly vpc: IVpc;
  private readonly userPool: IUserPool;
  private readonly lambdaEnv;
  private readonly lambdaRuntimePythonVersion: aws_lambda.Runtime = aws_lambda.Runtime.PYTHON_3_12;
  private serviceUserSecret: Secret;

  constructor(scope: Construct, id: string, props: StackProps & TokenServiceProps) {
    super(scope, id, props);
    this.props = props;

    this.vpc = Vpc.fromLookup(this, 'MainVpc', props.vpcProps);

    // NOTE:
    // Token Service has very high dependency on the upstream Cognito User Pool OAuth2 broker
    // AAI infrastructure. Having pre-existed Cognito resource setup within the target environment
    // is implicitly assumed. If this is no avail then fail it early with the Token Service
    // deployment. This is intentional.
    const userPoolId = this.getUserPoolId().stringValue;
    const userPoolAppClientId = this.getUserPoolAppClientId().stringValue;

    this.userPool = UserPool.fromUserPoolId(this, 'UserPool', userPoolId);

    this.lambdaEnv = {
      USER_POOL_ID: userPoolId,
      USER_POOL_APP_CLIENT_ID: userPoolAppClientId,
    };

    this.createServiceUserSecretWithRotation();
    this.createJWTSecretWithRotation();
  }

  private createServiceUserSecretWithRotation() {
    const lambdaRole = new Role(this, 'ServiceUserRole', {
      assumedBy: new ServicePrincipal('lambda.amazonaws.com'),
      description: 'Lambda execution role for ' + 'ServiceUserRole',
    });

    const lambdaLogGroup = new LogGroup(this, 'ServiceUserLogGroup');

    // create service user cred rotation function
    const userRotationFn = new PythonFunction(this, 'ServiceUserRotateFn', {
      entry: path.join(__dirname, '../token_service/'),
      index: 'rotate_service_user.py',
      handler: 'lambda_handler',
      runtime: this.lambdaRuntimePythonVersion,
      environment: this.lambdaEnv,
      vpc: this.vpc,
      vpcSubnets: { subnets: this.vpc.privateSubnets },
      architecture: Architecture.ARM_64,
      timeout: Duration.seconds(28),
      role: lambdaRole,
      logGroup: lambdaLogGroup,
    });
    lambdaLogGroup.grantWrite(userRotationFn);

    this.userPool.grant(
      userRotationFn,
      'cognito-idp:DescribeUserPool',
      // 'cognito-idp:AdminConfirmSignUp',
      // 'cognito-idp:AdminDeleteUser',
      // 'cognito-idp:AdminDisableUser',
      // 'cognito-idp:AdminEnableUser',
      'cognito-idp:AdminGetUser',
      'cognito-idp:AdminSetUserPassword',
      'cognito-idp:InitiateAuth',
      'cognito-idp:ListUserPools',
      'cognito-idp:ListUsers',
      'cognito-idp:SignUp'
    );

    // create token service user secret
    const serviceUserSecret: Secret = new Secret(this, 'ServiceUserSecret', {
      // just create a blank secret container first
      // the admin should populate after enrolling the service user registration elsewhere
      secretName: this.props.serviceUserSecretName,
    });

    serviceUserSecret.addRotationSchedule('ServiceUserRotationSchedule', {
      rotationLambda: userRotationFn,
      automaticallyAfter: Duration.days(7), // rotate service user cred every 7 days
      rotateImmediatelyOnUpdate: true,
    });

    this.serviceUserSecret = serviceUserSecret;
  }

  private createJWTSecretWithRotation() {
    const lambdaRole = new Role(this, 'JWTRole', {
      assumedBy: new ServicePrincipal('lambda.amazonaws.com'),
      description: 'Lambda execution role for ' + 'JWTRole',
    });

    const lambdaLogGroup = new LogGroup(this, 'JWTLogGroup');

    // create service user cred rotation function
    const jwtRotationFn = new PythonFunction(this, 'JWTRotateFn', {
      entry: path.join(__dirname, '../token_service/'),
      index: 'rotate_service_jwt.py',
      handler: 'lambda_handler',
      runtime: this.lambdaRuntimePythonVersion,
      environment: {
        ...this.lambdaEnv,
        SERVICE_USER_SECRET_ID: this.props.serviceUserSecretName,
        SERVICE_INFO_ENDPOINT: '', // TODO we need stable service info endpoint
      },
      vpc: this.vpc,
      vpcSubnets: { subnets: this.vpc.privateSubnets },
      architecture: Architecture.ARM_64,
      timeout: Duration.seconds(28),
      role: lambdaRole,
      logGroup: lambdaLogGroup,
    });
    lambdaLogGroup.grantWrite(jwtRotationFn);

    this.userPool.grant(jwtRotationFn, 'cognito-idp:InitiateAuth');

    // create token service user jwt secret
    const jwtSecret: Secret = new Secret(this, 'JWTSecret', {
      // it should get populated by rotation
      secretName: this.props.jwtSecretName,
    });

    jwtSecret.addRotationSchedule('ServiceUserRotationSchedule', {
      rotationLambda: jwtRotationFn,
      automaticallyAfter: Duration.hours(12), // rotate JWT every 12 hours
      rotateImmediatelyOnUpdate: true,
    });

    this.serviceUserSecret.grantRead(jwtRotationFn.role as Role); // allow read to service user secret
  }

  private getUserPoolId(): IStringParameter {
    /**
     * FIXME One fine day in future when we have proper Cognito AAI setup.
     *  For the moment, we leverage Portal and established Cognito infrastructure.
     *  See https://github.com/umccr/orcabus/issues/102
     */
    const SSM_USER_POOL_ID: string = '/data_portal/client/cog_user_pool_id';

    return aws_ssm.StringParameter.fromStringParameterName(
      this,
      'CognitoUserPoolIdParameter',
      SSM_USER_POOL_ID
    );
  }

  private getUserPoolAppClientId(): IStringParameter {
    /**
     * FIXME One fine day in future when we have proper Cognito AAI setup.
     *  For the moment, we leverage Portal and established Cognito infrastructure.
     *  See https://github.com/umccr/orcabus/issues/102
     */
    const SSM_PORTAL_CLIENT_ID: string = '/data_portal/client/data2/cog_app_client_id_stage';

    return aws_ssm.StringParameter.fromStringParameterName(
      this,
      'CognitoPortalClientIdParameter',
      SSM_PORTAL_CLIENT_ID
    );
  }
}
