import {
  AppStage,
  cognitoApiGatewayConfig,
  computeSecurityGroupName,
  corsAllowOrigins,
  logsApiGatewayConfig,
  vpcProps,
} from '../constants';
import { MetadataManagerStackProps } from '../../lib/workload/stateless/stacks/metadata-manager/deploy/stack';

export const getMetadataManagerStackProps = (stage: AppStage): MetadataManagerStackProps => {
  const isDailySync = stage == AppStage.PROD ? true : false;

  return {
    vpcProps,
    isDailySync: isDailySync,
    lambdaSecurityGroupName: computeSecurityGroupName,
    apiGatewayCognitoProps: {
      ...cognitoApiGatewayConfig,
      corsAllowOrigins: corsAllowOrigins[stage],
      apiGwLogsConfig: logsApiGatewayConfig[stage],
      apiName: 'MetadataManager',
      customDomainNamePrefix: 'metadata',
    },
  };
};
