# Authorization Stack

This stack contains resources that handle authorization requests.

## AWS Verified Permissions

The current stack deploys AWS Verified Permissions, defining an identity source and policies as described below. An HTTP Lambda Authorizer is included for use in stacks where routes/methods need to comply with this policy. The Lambda ARN is stored in an SSM Parameter String defined in `config/constants.ts` as the `authStackHttpLambdaAuthorizerParameterName` constant.

### Identity Source

- **UMCCR Cognito User Pool**

  Sourced from the UMCCR Cognito User Pool, defined in the infrastructure Terraform repository. The AWS Cognito User Pool
  is expected to have groups, which will be used in the policy. Note that the JWT must be generated with the
  latest token containing the proper Cognito group claims for it to work. This also applies when a user is removed from
  the group; the JWT must expire to become invalid.

### Group

Policies are currently assigned based on groups from the Cognito User Pool. The policies are defined in `stack.ts` within the class where the function is named `setup{GROUP_NAME}CedarPolicy`.

- **Admin**: For admins/service users (all actions are granted to this group).
- **Curators**: For curators (all policies are applied to all curators in this group).
- **Bioinfo**: For bioinformatics members.
