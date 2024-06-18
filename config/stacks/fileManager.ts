import { FilemanagerConfig } from '../../lib/workload/stateless/stacks/filemanager/deploy/stack';
import {
  AppStage,
  computeSecurityGroupName,
  databasePort,
  dbClusterEndpointHostParameterName,
  eventSourceQueueName,
  vpcProps,
  cognitoPortalAppClientIdParameterName,
  cognitoStatusPageAppClientIdParameterName,
  cognitoUserPoolIdParameterName,
  oncoanalyserBucket,
  icav2PipelineCacheBucket,
  fileManagerIngestRoleName,
} from '../constants';

export const getFileManagerStackProps = (stage: AppStage): FilemanagerConfig => {
  return {
    securityGroupName: computeSecurityGroupName,
    vpcProps,
    eventSourceQueueName: eventSourceQueueName,
    databaseClusterEndpointHostParameter: dbClusterEndpointHostParameterName,
    port: databasePort,
    migrateDatabase: true,
    cognitoPortalAppClientIdParameterName: cognitoPortalAppClientIdParameterName,
    cognitoStatusPageAppClientIdParameterName: cognitoStatusPageAppClientIdParameterName,
    cognitoUserPoolIdParameterName: cognitoUserPoolIdParameterName,
    inventorySourceBuckets: ['filemanager-inventory-test'],
    eventSourceBuckets: [oncoanalyserBucket[stage], icav2PipelineCacheBucket[stage]],
    fileManagerIngestRoleName: fileManagerIngestRoleName,
  };
};
