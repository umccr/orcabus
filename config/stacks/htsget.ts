import {
  AppStage,
  cognitoApiGatewayConfig,
  corsAllowOrigins,
  logsApiGatewayConfig,
  vpcProps,
} from '../constants';
import { HtsgetStackConfigurableProps } from '../../lib/workload/stateless/stacks/htsget/stack';

export const getHtsgetProps = (stage: AppStage): HtsgetStackConfigurableProps => {
  return {
    vpcProps,
    apiGatewayCognitoProps: {
      ...cognitoApiGatewayConfig,
      corsAllowOrigins: corsAllowOrigins[stage],
      apiGwLogsConfig: logsApiGatewayConfig[stage],
      apiName: 'Htsget',
      customDomainNamePrefix: 'htsget-file',
    },
  };
};
