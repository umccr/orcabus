import {
  AppStage,
  icav1AccessTokenSecretName,
  icav1BucketForBatchOpsReport,
  icav1BucketForCopyDestination,
  icav1BucketForCopyDestinationPrefix,
  icav1BucketForManifestOrInventory,
  icav1CopyBatchUtilityName,
  icav1TransferMaxErrorRetries,
  icav1TransferMaxPoolConnections,
  icav1TransferMaximumConcurrency,
  icav1TransferMultiPartChunkSize,
} from '../constants';

import { ICAv1CopyBatchUtilityConfig } from '../../lib/workload/stateless/stacks/icav1-copy-batch-utility/deploy/stack';

export const getICAv1CopyBatchUtilityStackProps = (
  stage: AppStage
): ICAv1CopyBatchUtilityConfig => {
  return {
    AppName: icav1CopyBatchUtilityName,
    Icav1TokenSecretId: icav1AccessTokenSecretName[stage],
    BucketForCopyDestination: icav1BucketForCopyDestination,
    BucketForCopyDestinationPrefix: icav1BucketForCopyDestinationPrefix,
    BucketForManifestOrInventory: icav1BucketForManifestOrInventory,
    BucketForBatchOpsReport: icav1BucketForBatchOpsReport,
    TransferMaximumConcurrency: icav1TransferMaximumConcurrency,
    TransferMaxPoolConnections: icav1TransferMaxPoolConnections,
    TransferMaxErrorRetries: icav1TransferMaxErrorRetries,
    TransferMultiPartChunkSize: icav1TransferMultiPartChunkSize,
  };
};
