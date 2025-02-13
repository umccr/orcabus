import { accessKeySecretName, accessKeySecretUserName, AppStage } from '../constants';
import { AccessKeySecretStackProps } from '../../lib/workload/stateful/stacks/access-key-secret';
import { Function as FMFunction } from '../../lib/workload/stateless/stacks/filemanager/deploy/constructs/functions/function';
import { fileManagerBuckets, fileManagerInventoryBuckets } from './fileManager';

export const getAccessKeySecretStackProps = (stage: AppStage): AccessKeySecretStackProps => {
  const inventorySourceBuckets = fileManagerInventoryBuckets(stage);
  const eventSourceBuckets = fileManagerBuckets(stage);

  return {
    userName: accessKeySecretUserName,
    secretName: accessKeySecretName,
    policies: FMFunction.formatPoliciesForBucket(
      [...eventSourceBuckets, ...inventorySourceBuckets],
      [...FMFunction.getObjectActions()]
    ),
  };
};
