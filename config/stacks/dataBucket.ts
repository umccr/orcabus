import { AppStage, accountIdAlias } from '../constants';
import { DataBucketStackProps } from '../../lib/workload/stateful/stacks/data/stack';

export const getDataBucketStackProps = (stage: AppStage): DataBucketStackProps => {
  switch (stage) {
    // Currently test-data bucket only used for dev purposes
    case AppStage.BETA:
      return {
        bucketName: `orcabus-test-data-${accountIdAlias.beta}-ap-southeast-2`,
      };

    case AppStage.GAMMA:
      return {};
    case AppStage.PROD:
      return {};
  }
};
