import { TokenServiceStackProps } from '../../lib/workload/stateful/stacks/token-service/deploy/stack';
import {
  cognitoPortalAppClientIdParameterName,
  cognitoUserPoolIdParameterName,
  jwtSecretName,
  serviceUserSecretName,
  vpcProps,
} from '../constants';

export const getTokenServiceStackProps = (): TokenServiceStackProps => {
  return {
    serviceUserSecretName: serviceUserSecretName,
    jwtSecretName: jwtSecretName,
    vpcProps: vpcProps,
    cognitoUserPoolIdParameterName: cognitoUserPoolIdParameterName,
    cognitoPortalAppClientIdParameterName: cognitoPortalAppClientIdParameterName,
  };
};
