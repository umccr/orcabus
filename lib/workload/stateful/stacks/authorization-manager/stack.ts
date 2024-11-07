import { Stack, StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { StringParameter } from 'aws-cdk-lib/aws-ssm';
import { CfnPolicyStore, CfnPolicy, CfnIdentitySource } from 'aws-cdk-lib/aws-verifiedpermissions';
import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';

import cedarSchemaJson from './cedarSchema.json';
import { Architecture, Runtime } from 'aws-cdk-lib/aws-lambda';
import path from 'path';
import { PolicyStatement } from 'aws-cdk-lib/aws-iam';

export interface AuthorizationManagerStackProps {
  cognito: CognitoConfig;
  authStackHttpLambdaAuthorizerParameterName: string;
}

interface CognitoConfig {
  /**
   * The SSM parameter name that cognito user pool ID is stored
   */
  userPoolIdParameterName: string;
  /**
   * The AWS region where the cognito user pool is deployed
   */
  region: string;
  /**
   * The AWS account number where the cognito user pool is deployed
   */
  accountNumber: string;
}

export class AuthorizationManagerStack extends Stack {
  constructor(scope: Construct, id: string, props: StackProps & AuthorizationManagerStackProps) {
    super(scope, id, props);

    // Amazon Verified Permission
    const policyStore = new CfnPolicyStore(this, 'VerifiedPermissionPolicyStore', {
      validationSettings: { mode: 'STRICT' },
      description: 'OrcaBus authorization policy',
      schema: {
        cedarJson: JSON.stringify(cedarSchemaJson),
      },
    });

    this.setupCognitoIntegrationAndPolicy({
      cognito: props.cognito,
      policyStoreId: policyStore.attrPolicyStoreId,
    });

    this.setupTokenLambdaAuthorization({
      policyStoreARN: policyStore.attrArn,
      policyStoreId: policyStore.attrPolicyStoreId,
      authStackHttpLambdaAuthorizerParameterName: props.authStackHttpLambdaAuthorizerParameterName,
    });
  }

  /**
   * This sets up the Verified Permissions integration with Cognito.
   * It sources users from the Cognito user pool and creates a static policy
   * that grants all permissions to users in the admin group within the user pool.
   *
   * @param props Cognito properties
   */
  private setupCognitoIntegrationAndPolicy(props: {
    policyStoreId: string;
    cognito: CognitoConfig;
  }) {
    // Grab the user pool ID from SSM
    const userPoolId = StringParameter.fromStringParameterName(
      this,
      'CognitoUserPoolIdStringParameter',
      props.cognito.userPoolIdParameterName
    ).stringValue;

    // Allow the policy store to source the identity from existing Cognito User Pool Id
    new CfnIdentitySource(this, 'VerifiedPermissionIdentitySource', {
      configuration: {
        cognitoUserPoolConfiguration: {
          userPoolArn: `arn:aws:cognito-idp:${props.cognito.region}:${props.cognito.accountNumber}:userpool/${userPoolId}`,
          groupConfiguration: {
            groupEntityType: 'OrcaBus::CognitoUserGroup', // Refer to './cedarSchema.json'
          },
        },
      },
      principalEntityType: 'OrcaBus::User',
      policyStoreId: props.policyStoreId,
    });

    // Create a static policy that allow user from the admin group to allow all actions
    new CfnPolicy(this, 'CognitoPortalAdminPolicy', {
      definition: {
        static: {
          statement: `
            permit (
              principal in OrcaBus::CognitoUserGroup::"${userPoolId}|admin",
              action,
              resource
            );
          `,
          description:
            'Allow all action for all resource for user in the admin cognito user pool group',
        },
      },
      policyStoreId: props.policyStoreId,
    });
  }

  private setupTokenLambdaAuthorization(props: {
    policyStoreId: string;
    policyStoreARN: string;
    authStackHttpLambdaAuthorizerParameterName: string;
  }) {
    const lambdaAuth = new PythonFunction(this, 'HTTPAuthorizerLambda', {
      entry: path.join(__dirname, 'http-lambda-authorizer'),
      architecture: Architecture.ARM_64,
      runtime: Runtime.PYTHON_3_12,
      index: 'http_authorizer.py',
      retryAttempts: 0,
      environment: { POLICY_STORE_ID: props.policyStoreId },
      initialPolicy: [
        new PolicyStatement({
          actions: ['verifiedpermissions:IsAuthorizedWithToken'],
          resources: [props.policyStoreARN],
        }),
      ],
    });

    new StringParameter(this, 'HTTPAuthorizerLambdaARNParameter', {
      parameterName: props.authStackHttpLambdaAuthorizerParameterName,
      description:
        'ARN of the HTTP lambda authorizer that allow access defined in Amazon Verified Permission',
      stringValue: lambdaAuth.functionArn,
    });
  }
}
