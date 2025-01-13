import { SampleSheetCheckerStackProps } from '../../lib/workload/stateless/stacks/sample-sheet-check/stack';
import {
  AppStage,
  cognitoApiGatewayConfig,
  corsAllowOrigins,
  logsApiGatewayConfig,
} from '../constants';

export const getSampleSheetCheckerProps = (stage: AppStage): SampleSheetCheckerStackProps => {
  return {
    apiGatewayConstructProps: {
      ...cognitoApiGatewayConfig,
      corsAllowOrigins: corsAllowOrigins[stage],
      apiGwLogsConfig: logsApiGatewayConfig[stage],
      apiName: 'SSCheck',
      customDomainNamePrefix: 'sscheck-orcabus',
    },
  };
};
