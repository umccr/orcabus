import {
  AppStage,
  vpcProps,
  oncoanalyserBucket,
  icav2PipelineCacheBucket,
  dataMoverRoleName,
  icav2ArchiveAnalysisBucket,
  icav2ArchiveFastqBucket,
  fileManagerInventoryBucket,
  logsApiGatewayConfig,
} from '../constants';
import { DataMigrateStackProps } from '../../lib/workload/stateless/stacks/data-migrate/deploy/stack';

export const getDataMigrateStackProps = (stage: AppStage): DataMigrateStackProps => {
  // For dev/staging we can write to any bucket that is also readable.
  let writeToBuckets = [oncoanalyserBucket[stage], icav2PipelineCacheBucket[stage]];
  switch (stage) {
    case AppStage.BETA:
      // For dev additionally, write to the filemanager inventory bucket for testing.
      writeToBuckets.push(fileManagerInventoryBucket[stage]);
      break;
    case AppStage.PROD:
      // For prod, we only allow writing to the archive buckets, nothing else.
      writeToBuckets = [icav2ArchiveAnalysisBucket[stage], icav2ArchiveFastqBucket[stage]];
      break;
  }

  return {
    vpcProps,
    dataMoverRoleName,
    deleteFromBuckets: [oncoanalyserBucket[stage], icav2PipelineCacheBucket[stage]],
    readFromBuckets: [oncoanalyserBucket[stage], icav2PipelineCacheBucket[stage]],
    writeToBuckets,
    logRetention: logsApiGatewayConfig[stage].retention,
  };
};
