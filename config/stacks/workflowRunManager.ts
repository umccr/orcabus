import { WorkflowManagerStackProps } from '../../lib/workload/stateless/stacks/workflow-manager/deploy/stack';
import {
  vpcProps,
  computeSecurityGroupName,
  eventBusName,
  cognitoUserPoolIdParameterName,
  cognitoPortalAppClientIdParameterName,
  cognitoStatusPageAppClientIdParameterName,
} from '../constants';

export const getWorkflowManagerStackProps = (): WorkflowManagerStackProps => {
  return {
    vpcProps,
    lambdaSecurityGroupName: computeSecurityGroupName,
    mainBusName: eventBusName,
    cognitoUserPoolIdParameterName: cognitoUserPoolIdParameterName,
    cognitoPortalAppClientIdParameterName: cognitoPortalAppClientIdParameterName,
    cognitoStatusPageAppClientIdParameterName: cognitoStatusPageAppClientIdParameterName,
  };
};
