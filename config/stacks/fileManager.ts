import { FilemanagerConfig } from '../../lib/workload/stateless/stacks/filemanager/deploy/stack';
import {
  AppStage,
  cognitoApiGatewayConfig,
  computeSecurityGroupName,
  corsAllowOrigins,
  databasePort,
  dbClusterEndpointHostParameterName,
  eventSourceQueueName,
  fileManagerIngestRoleName,
  fileManagerInventoryBucket,
  icav2ArchiveAnalysisBucket,
  icav2ArchiveFastqBucket,
  icav2PipelineCacheBucket,
  logsApiGatewayConfig,
  oncoanalyserBucket,
  vpcProps,
} from '../constants';

export const getFileManagerStackProps = (stage: AppStage): FilemanagerConfig => {
  const inventorySourceBuckets = [];
  if (stage == AppStage.BETA) {
    inventorySourceBuckets.push(fileManagerInventoryBucket[stage]);
  }

  const eventSourceBuckets = [oncoanalyserBucket[stage], icav2PipelineCacheBucket[stage]];
  if (stage == AppStage.PROD) {
    eventSourceBuckets.push(icav2ArchiveAnalysisBucket[stage]);
    eventSourceBuckets.push(icav2ArchiveFastqBucket[stage]);
  }

  return {
    securityGroupName: computeSecurityGroupName,
    vpcProps,
    eventSourceQueueName: eventSourceQueueName,
    databaseClusterEndpointHostParameter: dbClusterEndpointHostParameterName,
    port: databasePort,
    migrateDatabase: true,
    inventorySourceBuckets,
    eventSourceBuckets,
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
