import {
  cognitoPortalAppClientIdParameterName,
  cognitoStatusPageAppClientIdParameterName,
  cognitoUserPoolIdParameterName,
  computeSecurityGroupName,
  eventBusName,
  vpcProps,
} from '../constants';
import { SequenceRunManagerStackProps } from '../../lib/workload/stateless/stacks/sequence-run-manager/deploy/stack';

export const getSequenceRunManagerStackProps = (): SequenceRunManagerStackProps => {
  return {
    vpcProps,
    lambdaSecurityGroupName: computeSecurityGroupName,
    mainBusName: eventBusName,
    cognitoUserPoolIdParameterName: cognitoUserPoolIdParameterName,
    cognitoPortalAppClientIdParameterName: cognitoPortalAppClientIdParameterName,
    cognitoStatusPageAppClientIdParameterName: cognitoStatusPageAppClientIdParameterName,
  };
};
