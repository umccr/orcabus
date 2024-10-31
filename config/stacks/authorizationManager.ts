import { AuthorizationManagerStackProps } from '../../lib/workload/stateful/stacks/authorization-manager/stack';
import {
  cognitoUserPoolIdParameterName,
  region,
  accountIdAlias,
  AppStage,
  adminHttpLambdaAuthorizerParameterName,
} from '../constants';

export const getAuthorizationManagerStackProps = (
  stage: AppStage
): AuthorizationManagerStackProps => {
  return {
    cognito: {
      userPoolIdParameterName: cognitoUserPoolIdParameterName,
      region: region,
      accountNumber: accountIdAlias[stage],
    },
    adminHttpLambdaAuthorizerParameterName: adminHttpLambdaAuthorizerParameterName,
  };
};
