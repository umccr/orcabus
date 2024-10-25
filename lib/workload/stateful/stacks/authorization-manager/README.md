# Authorization Stack

This stack contains resources that handle authorization requests.

## AWS Verified Permissions

The current stack deploys AWS Verified Permissions, defining an identity source and policies as described below. A HTTP Lambda Authorizer is also included for use with other stacks.

### Identity Source

- **UMCCR Cognito User Pool**

  Sourced from the UMCCR Cognito User Pool, defined in the infrastructure Terraform repository. The AWS Cognito User Pool
  is expected to have an `admin` group, which will be used in the policy. Note that the JWT must be generated with the
  latest token containing the proper Cognito group claims for it to work. This also applies when a user is removed from
  the group; the JWT must expire to become invalid.

### Policy

- **AdminPolicy**

  A static policy defined in the stack that allows anyone in the `admin` group of the Cognito user pool to perform any action. This essentially checks if a user is in the group, integrated with the Cognito setup.

  The HTTP Lambda Authorizer is also defined for use in stacks where routes/methods need to comply with this policy. The
  Lambda ARN is stored in SSM Parameter String defined in `config/constants.ts` as the `adminHttpLambdaAuthorizerParameterName` constant.
