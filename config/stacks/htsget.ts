import {
  AppStage,
  cognitoApiGatewayConfig,
  corsAllowOrigins,
  fileManagerIngestRoleName,
  logsApiGatewayConfig,
  vpcProps,
} from '../constants';
import { HtsgetStackProps } from '../../lib/workload/stateless/stacks/htsget/stack';
import { fileManagerBuckets, fileManagerInventoryBuckets } from './fileManager';

export const getHtsgetProps = (stage: AppStage): HtsgetStackProps => {
  const inventorySourceBuckets = fileManagerInventoryBuckets(stage);
  const eventSourceBuckets = fileManagerBuckets(stage);

  return {
    vpcProps,
    apiGatewayCognitoProps: {
      ...cognitoApiGatewayConfig,
      corsAllowOrigins: corsAllowOrigins[stage],
      apiGwLogsConfig: logsApiGatewayConfig[stage],
      apiName: 'Htsget',
      customDomainNamePrefix: 'htsget-file',
    },
    buckets: [...inventorySourceBuckets, ...eventSourceBuckets],
    roleName: fileManagerIngestRoleName,
  };
};
