import { AppStage, region } from './constants';
import { StatefulStackCollectionProps } from '../lib/workload/stateful/statefulStackCollectionClass';
import { StatelessStackCollectionProps } from '../lib/workload/stateless/statelessStackCollectionClass';
import { getSharedStackProps } from './stacks/shared';
import { getIcaEventPipeStackProps } from './stacks/icaEventPipe';
import { getTokenServiceStackProps } from './stacks/tokenService';
import { getPostgresManagerStackProps } from './stacks/postgresManager';
import { getMetadataManagerStackProps } from './stacks/metadataManager';
import { getSequenceRunManagerStackProps } from './stacks/sequenceRunManager';
import { getFileManagerStackProps } from './stacks/fileManager';
import { getBsRunsUploadManagerStackProps } from './stacks/bsRunsUploadManager';
import { getICAv2CopyBatchUtilityStackProps } from './stacks/icav2CopyBatchUtility';

interface EnvironmentConfig {
  name: string;
  region: string;
  accountId: string;
  stackProps: {
    statefulConfig: StatefulStackCollectionProps;
    statelessConfig: StatelessStackCollectionProps;
  };
}

/**
 * The function will return the appropriate configuration for the given account
 *
 * @param s the name of account stage
 * @returns the configuration for the given s
 */
export const getEnvironmentConfig = (s: AppStage): EnvironmentConfig | null => {
  switch (s) {
    case AppStage.BETA:
      return {
        name: 'beta',
        region,
        accountId: '843407916570', // umccr_development
        stackProps: {
          statefulConfig: {
            sharedStackProps: getSharedStackProps(s),
            tokenServiceStackProps: getTokenServiceStackProps(),
            icaEventPipeStackProps: getIcaEventPipeStackProps(),
          },
          statelessConfig: {
            postgresManagerStackProps: getPostgresManagerStackProps(),
            metadataManagerStackProps: getMetadataManagerStackProps(),
            sequenceRunManagerStackProps: getSequenceRunManagerStackProps(),
            fileManagerStackProps: getFileManagerStackProps(s),
            bsRunsUploadManagerStackProps: getBsRunsUploadManagerStackProps(s),
            icav2CopyBatchUtilityStackProps: getICAv2CopyBatchUtilityStackProps(s),
          },
        },
      };

    case AppStage.GAMMA:
      return {
        name: 'gamma',
        region,
        accountId: '455634345446', // umccr_staging
        stackProps: {
          statefulConfig: {
            sharedStackProps: getSharedStackProps(s),
            tokenServiceStackProps: getTokenServiceStackProps(),
            icaEventPipeStackProps: getIcaEventPipeStackProps(),
          },
          statelessConfig: {
            postgresManagerStackProps: getPostgresManagerStackProps(),
            metadataManagerStackProps: getMetadataManagerStackProps(),
            sequenceRunManagerStackProps: getSequenceRunManagerStackProps(),
            fileManagerStackProps: getFileManagerStackProps(s),
            bsRunsUploadManagerStackProps: getBsRunsUploadManagerStackProps(s),
            icav2CopyBatchUtilityStackProps: getICAv2CopyBatchUtilityStackProps(s),
          },
        },
      };

    case AppStage.PROD:
      return {
        name: 'prod',
        region,
        accountId: '472057503814', // umccr_production
        stackProps: {
          statefulConfig: {
            sharedStackProps: getSharedStackProps(s),
            tokenServiceStackProps: getTokenServiceStackProps(),
            icaEventPipeStackProps: getIcaEventPipeStackProps(),
          },
          statelessConfig: {
            postgresManagerStackProps: getPostgresManagerStackProps(),
            metadataManagerStackProps: getMetadataManagerStackProps(),
            sequenceRunManagerStackProps: getSequenceRunManagerStackProps(),
            fileManagerStackProps: getFileManagerStackProps(s),
            bsRunsUploadManagerStackProps: getBsRunsUploadManagerStackProps(s),
            icav2CopyBatchUtilityStackProps: getICAv2CopyBatchUtilityStackProps(s),
          },
        },
      };
  }
};
