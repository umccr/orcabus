import { FilemanagerConfig } from '../../lib/workload/stateless/stacks/filemanager/deploy/stack';
import {
  AppStage,
  computeSecurityGroupName,
  databasePort,
  dbClusterEndpointHostParameterName,
  eventSourceQueueName,
  vpcProps,
  oncoanalyserBucket,
  icav2PipelineCacheBucket,
  fileManagerIngestRoleName,
  logsApiGatewayConfig,
  cognitoApiGatewayConfig,
  corsAllowOrigins,
} from '../constants';

export const getFileManagerStackProps = (stage: AppStage): FilemanagerConfig => {
  return {
    securityGroupName: computeSecurityGroupName,
    vpcProps,
    eventSourceQueueName: eventSourceQueueName,
    databaseClusterEndpointHostParameter: dbClusterEndpointHostParameterName,
    port: databasePort,
    migrateDatabase: true,
    inventorySourceBuckets: ['filemanager-inventory-test'],
    eventSourceBuckets: [oncoanalyserBucket[stage], icav2PipelineCacheBucket[stage]],
    fileManagerRoleName: fileManagerIngestRoleName,
    apiGatewayCognitoProps: {
      ...cognitoApiGatewayConfig,
      corsAllowOrigins: corsAllowOrigins[stage],
      apiGwLogsConfig: logsApiGatewayConfig[stage],
      apiName: 'FileManager',
      customDomainNamePrefix: 'file',
    },
  };
};
