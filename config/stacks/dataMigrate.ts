import {
  AppStage,
  dataMoverRoleName,
  fileManagerInventoryBucket,
  icav2ArchiveAnalysisBucket,
  icav2ArchiveFastqBucket,
  icav2PipelineCacheBucket,
  logsApiGatewayConfig,
  oncoanalyserBucket,
  vpcProps,
} from '../constants';
import { DataMigrateStackProps } from '../../lib/workload/stateless/stacks/data-migrate/deploy/stack';

export const getDataMigrateStackProps = (stage: AppStage): DataMigrateStackProps => {
  let readFromBuckets = [];
  let deleteFromBuckets = [];
  let writeToBuckets = [];
  switch (stage) {
    case AppStage.BETA:
      // For dev/staging we can write to and read from the same set of buckets.
      readFromBuckets = [oncoanalyserBucket[stage], icav2PipelineCacheBucket[stage]];
      deleteFromBuckets = [oncoanalyserBucket[stage], icav2PipelineCacheBucket[stage]];

      // For dev additionally, write to the filemanager inventory bucket for testing.
      writeToBuckets = [
        oncoanalyserBucket[stage],
        icav2PipelineCacheBucket[stage],
        fileManagerInventoryBucket[stage],
      ];
      break;
    case AppStage.GAMMA:
      readFromBuckets = [oncoanalyserBucket[stage], icav2PipelineCacheBucket[stage]];
      deleteFromBuckets = [oncoanalyserBucket[stage], icav2PipelineCacheBucket[stage]];

      writeToBuckets = [oncoanalyserBucket[stage], icav2PipelineCacheBucket[stage]];
      break;
    case AppStage.PROD:
      readFromBuckets = [oncoanalyserBucket[stage], icav2PipelineCacheBucket[stage]];
      deleteFromBuckets = [oncoanalyserBucket[stage], icav2PipelineCacheBucket[stage]];

      // For prod, we only allow writing to the archive buckets, nothing else.
      writeToBuckets = [icav2ArchiveAnalysisBucket[stage], icav2ArchiveFastqBucket[stage]];
      break;
  }

  return {
    vpcProps,
    dataMoverRoleName,
    deleteFromBuckets,
    readFromBuckets,
    writeToBuckets,
    logRetention: logsApiGatewayConfig[stage].retention,
  };
};
