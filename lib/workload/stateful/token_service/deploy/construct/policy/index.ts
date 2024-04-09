import { AnyPrincipal, Effect, PolicyStatement } from 'aws-cdk-lib/aws-iam';

// --- common policy

export function getLambdaBasicExecPolicy(resources: string[]) {
  /**
   * NOTE: If you deterministically create the LogGroup resource and, assign it to your Lambda
   * function then you would not need to use this policy. You just need to grant write this LogGroup
   * by your Lambda function. e.g. `lambdaLogGroup.grantWrite(userRotationFn);`
   *
   * Based on managed policies:
   * https://docs.aws.amazon.com/aws-managed-policy/latest/reference/AWSLambdaBasicExecutionRole.html
   */
  return new PolicyStatement({
    sid: 'LambdaBasicExecStmt1711498867457',
    effect: Effect.ALLOW,
    actions: ['logs:CreateLogGroup', 'logs:CreateLogStream', 'logs:PutLogEvents'],
    resources: resources,
  });
}

export function getLambdaVPCPolicy() {
  /**
   * NOTE: It is a bit challenging to restrict the ec2 resources here. These resourcs are nested
   * under specific VPC. The simply restricting to VPC ARN won't do. See below:
   * https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazonec2.html
   *
   * So, we have to allow '*' this case. Something to catch up in next AWS meetup, perhaps! ~victor
   *
   * Based on managed policies:
   * https://docs.aws.amazon.com/aws-managed-policy/latest/reference/AWSLambdaVPCAccessExecutionRole.html
   */
  return new PolicyStatement({
    sid: 'LambdaVPCStmt1711498867457',
    effect: Effect.ALLOW,
    actions: [
      'ec2:CreateNetworkInterface',
      'ec2:DescribeNetworkInterfaces',
      'ec2:DescribeSubnets',
      'ec2:DeleteNetworkInterface',
      'ec2:AssignPrivateIpAddresses',
      'ec2:UnassignPrivateIpAddresses',
    ],
    resources: ['*'], // see docstring ^^
  });
}

export function getSSMPolicy(resources: string[]) {
  /**
   * Based on managed policies:
   * https://docs.aws.amazon.com/aws-managed-policy/latest/reference/AmazonSSMReadOnlyAccess.html
   */
  return new PolicyStatement({
    sid: 'SSMStmt1711498867457',
    effect: Effect.ALLOW,
    actions: ['ssm:Describe*', 'ssm:Get*', 'ssm:List*'],
    resources: resources,
  });
}

// --- specific to Token Service application

export const getCognitoAdminActions = () => {
  // It is just `TypeScript - Arrow Functions` syntactic sugar. Nothing majorly special.
  // Same effect as any other classic function declaration syntax.
  /**
   * Always return new string array of permission flags that is allowed.
   */
  return [
    'cognito-idp:DescribeUserPool',
    'cognito-idp:AdminGetUser',
    'cognito-idp:AdminSetUserPassword',
    'cognito-idp:InitiateAuth',
    'cognito-idp:ListUserPools',
    'cognito-idp:ListUsers',
  ];
};

export function getCognitoAdminPolicy(resources: string[]) {
  /**
   * The Cognito policy that specifically required for Token Service `cognitor.py` application
   */
  return new PolicyStatement({
    sid: 'CognitoAdminStmt1711498867457',
    effect: Effect.ALLOW,
    actions: getCognitoAdminActions(),
    resources: resources,
  });
}

export const getCognitoJWTActions = () => {
  /**
   * Always return new string array of permission flags that is allowed.
   */
  return ['cognito-idp:InitiateAuth'];
};

export function getCognitoJWTPolicy(resources: string[]) {
  /**
   * The Cognito policy that specifically required for Token Service `cognitor.py` application
   */
  return new PolicyStatement({
    sid: 'CognitoJWTStmt1711498867457',
    effect: Effect.ALLOW,
    actions: getCognitoJWTActions(),
    resources: resources,
  });
}

export function getServiceUserSecretResourcePolicy(resources: string[]) {
  /**
   * NOTE: This policy rule is deny all & conditional exception on pass-in principal ARN resources.
   *
   * No one except rotation function role should have access to get service user secret
   *
   * REF:
   * https://github.com/umccr/infrastructure/blob/b731a87561cee99bf27545c65e98a38f1035f987/cdk/apps/ica_credentials/secrets/infrastructure.py#L85-L123
   * https://stackoverflow.com/questions/63915906/aws-secrets-manager-resource-policy-to-deny-all-roles-except-one-role
   */
  return new PolicyStatement({
    principals: [new AnyPrincipal()],
    effect: Effect.DENY,
    actions: ['secretsmanager:GetSecretValue'],
    resources: ['*'],
    conditions: {
      'ForAllValues:StringNotEquals': {
        'aws:PrincipalArn': resources,
      },
    },
  });
}