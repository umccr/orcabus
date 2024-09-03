import {
  AppStage,
  cognitoApiGatewayConfig,
  computeSecurityGroupName,
  corsAllowOrigins,
  eventBusName,
  logsApiGatewayConfig,
  vpcProps,
} from '../constants';
import { SequenceRunManagerStackProps } from '../../lib/workload/stateless/stacks/sequence-run-manager/deploy/stack';

export const getSequenceRunManagerStackProps = (stage: AppStage): SequenceRunManagerStackProps => {
  return {
    vpcProps,
    lambdaSecurityGroupName: computeSecurityGroupName,
    mainBusName: eventBusName,
    apiGatewayCognitoProps: {
      ...cognitoApiGatewayConfig,
      corsAllowOrigins: corsAllowOrigins[stage],
      apiGwLogsConfig: logsApiGatewayConfig[stage],
      apiName: 'SequenceRunManager',
      customDomainNamePrefix: 'sequence',
    },
  };
};
