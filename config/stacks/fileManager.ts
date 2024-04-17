import { FilemanagerConfig } from '../../lib/workload/stateless/stacks/filemanager/deploy/lib/filemanager';
import {
  AccountName,
  computeSecurityGroupName,
  databasePort,
  dbClusterEndpointHostParameterName,
  devBucket,
  eventSourceQueueName,
  prodBucket,
  stgBucket,
  vpcProps,
} from '../constants';

export const getFileManagerStackProps = (n: AccountName): FilemanagerConfig => {
  const baseConfig = {
    securityGroupName: computeSecurityGroupName,
    vpcProps,
    eventSourceQueueName: eventSourceQueueName,
    databaseClusterEndpointHostParameter: dbClusterEndpointHostParameterName,
    port: databasePort,
    migrateDatabase: true,
  };

  switch (n) {
    case 'beta':
      return {
        ...baseConfig,
        eventSourceBuckets: [devBucket],
      };
    case 'gamma':
      return {
        ...baseConfig,
        eventSourceBuckets: [stgBucket],
      };
    case 'prod':
      return {
        ...baseConfig,
        eventSourceBuckets: [prodBucket],
      };
  }
};
