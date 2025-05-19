import { FilemanagerConfig } from '../../lib/workload/stateless/stacks/filemanager/deploy/stack';
import {
  fileManagerPresignUserSecret,
  accountIdAlias,
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
  region,
  vpcProps,
  ntsmBucket,
  dataSharingCacheBucket,
  externalProjectBuckets,
  fileManagerDomainPrefix,
} from '../constants';

export const fileManagerBuckets = (stage: AppStage): string[] => {
  const eventSourceBuckets = [oncoanalyserBucket[stage], icav2PipelineCacheBucket[stage]];
  // Note, that we only archive production data, so we only need access to the archive buckets in prod.
  if (stage == AppStage.PROD) {
    eventSourceBuckets.push(icav2ArchiveAnalysisBucket[stage]);
    eventSourceBuckets.push(icav2ArchiveFastqBucket[stage]);
  }
  eventSourceBuckets.push(ntsmBucket[stage]);
  eventSourceBuckets.push(dataSharingCacheBucket[stage]);

  /* Extend the event source buckets with the external project buckets */
  for (const bucket of externalProjectBuckets[stage]) {
    eventSourceBuckets.push(bucket);
  }

  return eventSourceBuckets;
};

export const fileManagerInventoryBuckets = (stage: AppStage): string[] => {
  const inventorySourceBuckets = [];
  if (stage == AppStage.BETA) {
    inventorySourceBuckets.push(fileManagerInventoryBucket[stage]);
  }
  return inventorySourceBuckets;
};

export const getFileManagerStackProps = (stage: AppStage): FilemanagerConfig => {
  const inventorySourceBuckets = fileManagerInventoryBuckets(stage);
  const eventSourceBuckets = fileManagerBuckets(stage);

  return {
    securityGroupName: computeSecurityGroupName,
    vpcProps,
    eventSourceQueueName: eventSourceQueueName,
    databaseClusterEndpointHostParameter: dbClusterEndpointHostParameterName,
    port: databasePort,
    migrateDatabase: true,
    accessKeySecretArn: `arn:aws:secretsmanager:${region}:${accountIdAlias[stage]}:secret:${fileManagerPresignUserSecret}`, // pragma: allowlist secret
    inventorySourceBuckets,
    eventSourceBuckets,
    fileManagerRoleName: fileManagerIngestRoleName,
    apiGatewayCognitoProps: {
      ...cognitoApiGatewayConfig,
      corsAllowOrigins: corsAllowOrigins[stage],
      apiGwLogsConfig: logsApiGatewayConfig[stage],
      apiName: 'FileManager',
      customDomainNamePrefix: fileManagerDomainPrefix,
    },
  };
};
