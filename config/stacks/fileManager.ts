import { FilemanagerConfig } from '../../lib/workload/stateless/stacks/filemanager/deploy/stack';
import {
  AppStage,
  computeSecurityGroupName,
  databasePort,
  dbClusterEndpointHostParameterName,
  devBucket,
  eventSourceQueueName,
  prodBucket,
  stgBucket,
  vpcProps,
  cognitoPortalAppClientIdParameterName,
  cognitoStatusPageAppClientIdParameterName,
  cognitoUserPoolIdParameterName,
} from '../constants';

export const getFileManagerStackProps = (stage: AppStage): FilemanagerConfig => {
  const baseConfig = {
    securityGroupName: computeSecurityGroupName,
    vpcProps,
    eventSourceQueueName: eventSourceQueueName,
    databaseClusterEndpointHostParameter: dbClusterEndpointHostParameterName,
    port: databasePort,
    migrateDatabase: true,
    cognitoPortalAppClientIdParameterName: cognitoPortalAppClientIdParameterName,
    cognitoStatusPageAppClientIdParameterName: cognitoStatusPageAppClientIdParameterName,
    cognitoUserPoolIdParameterName: cognitoUserPoolIdParameterName,
  };

  switch (stage) {
    case AppStage.BETA:
      return {
        ...baseConfig,
        eventSourceBuckets: [devBucket],
      };
    case AppStage.GAMMA:
      return {
        ...baseConfig,
        eventSourceBuckets: [stgBucket],
      };
    case AppStage.PROD:
      return {
        ...baseConfig,
        eventSourceBuckets: [prodBucket],
      };
  }
};
