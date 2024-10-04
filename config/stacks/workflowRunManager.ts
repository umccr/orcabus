import { WorkflowManagerStackProps } from '../../lib/workload/stateless/stacks/workflow-manager/deploy/stack';
import {
  vpcProps,
  computeSecurityGroupName,
  eventBusName,
  AppStage,
  cognitoApiGatewayConfig,
  logsApiGatewayConfig,
  corsAllowOrigins,
} from '../constants';

export const getWorkflowManagerStackProps = (stage: AppStage): WorkflowManagerStackProps => {
  return {
    vpcProps,
    lambdaSecurityGroupName: computeSecurityGroupName,
    mainBusName: eventBusName,
    apiGatewayCognitoProps: {
      ...cognitoApiGatewayConfig,
      corsAllowOrigins: corsAllowOrigins[stage],
      apiGwLogsConfig: logsApiGatewayConfig[stage],
      apiName: 'WorkflowManager',
      customDomainNamePrefix: 'workflow',
    },
  };
};
