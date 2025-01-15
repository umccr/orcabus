import { SampleSheetCheckerStackProps } from '../../lib/workload/stateless/stacks/sample-sheet-check/stack';
import {
  AppStage,
  cognitoApiGatewayConfig,
  corsAllowOrigins,
  logsApiGatewayConfig,
} from '../constants';

export const getSampleSheetCheckerProps = (stage: AppStage): SampleSheetCheckerStackProps => {
  const metadataDomainNameDict = {
    [AppStage.BETA]: 'metadata.dev.umccr.org',
    [AppStage.GAMMA]: 'metadata.stg.umccr.org',
    [AppStage.PROD]: 'metadata.prod.umccr.org',
  };

  return {
    apiGatewayConstructProps: {
      ...cognitoApiGatewayConfig,
      corsAllowOrigins: corsAllowOrigins[stage],
      apiGwLogsConfig: logsApiGatewayConfig[stage],
      apiName: 'SSCheck',
      customDomainNamePrefix: 'sscheck-orcabus',
    },
    metadataDomainName: metadataDomainNameDict[stage],
  };
};
