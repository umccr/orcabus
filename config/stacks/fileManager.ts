import { RetentionDays } from 'aws-cdk-lib/aws-logs';
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
  corsAllowOrigins,
} from '../constants';
import { RemovalPolicy } from 'aws-cdk-lib';

export const getFileManagerStackProps = (stage: AppStage): FilemanagerConfig => {
  const logsConfig = {
    retention: stage === AppStage.PROD ? RetentionDays.TWO_YEARS : RetentionDays.TWO_WEEKS,
    removalPolicy: stage === AppStage.PROD ? RemovalPolicy.RETAIN : RemovalPolicy.DESTROY,
  };

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
    apiGwLogsConfig: logsConfig,
    inventorySourceBuckets: ['filemanager-inventory-test'],
    eventSourceBuckets: [oncoanalyserBucket[stage], icav2PipelineCacheBucket[stage]],
    fileManagerIngestRoleName: fileManagerIngestRoleName,
    corsAllowOrigins,
  };
};
