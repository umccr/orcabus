import { fileManagerPresignUserSecret, fileManagerPresignUser, AppStage } from '../constants';
import { AccessKeySecretStackProps } from '../../lib/workload/stateful/stacks/access-key-secret';
import { Role as FMRole } from '../../lib/workload/stateless/stacks/filemanager/deploy/constructs/functions/role';
import { fileManagerBuckets, fileManagerInventoryBuckets } from './fileManager';

export const getAccessKeySecretStackProps = (stage: AppStage): AccessKeySecretStackProps => {
  const inventorySourceBuckets = fileManagerInventoryBuckets(stage);
  const eventSourceBuckets = fileManagerBuckets(stage);

  return {
    userName: fileManagerPresignUser,
    secretName: fileManagerPresignUserSecret,
    policies: FMRole.formatPoliciesForBucket(
      // Only need read only access to the buckets. The filemanager will only use this access key for pre-signing URLs.
      // All regular actions will use the role.
      [...eventSourceBuckets, ...inventorySourceBuckets],
      [...FMRole.getObjectActions()]
    ),
  };
};
