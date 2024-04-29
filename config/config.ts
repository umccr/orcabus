import { region, accountIdAlias } from './constants';
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
 * @param accountName the name of account stage
 * @returns the configuration for the given accountName
 */
export const getEnvironmentConfig = (
  accountName: 'beta' | 'gamma' | 'prod'
): EnvironmentConfig | null => {
  switch (accountName) {
    case 'beta':
      return {
        name: 'beta',
        region,
        accountId: accountIdAlias[accountName], // umccr_development
        stackProps: {
          statefulConfig: {
            sharedStackProps: getSharedStackProps(accountName),
            tokenServiceStackProps: getTokenServiceStackProps(),
            icaEventPipeStackProps: getIcaEventPipeStackProps(),
          },
          statelessConfig: {
            postgresManagerStackProps: getPostgresManagerStackProps(),
            metadataManagerStackProps: getMetadataManagerStackProps(),
            sequenceRunManagerStackProps: getSequenceRunManagerStackProps(),
            fileManagerStackProps: getFileManagerStackProps(accountName),
            bsRunsUploadManagerStackProps: getBsRunsUploadManagerStackProps(accountName),
            icav2CopyBatchUtilityStackProps: getICAv2CopyBatchUtilityStackProps(accountName),
          },
        },
      };

    case 'gamma':
      return {
        name: 'gamma',
        region,
        accountId: accountIdAlias[accountName], // umccr_staging
        stackProps: {
          statefulConfig: {
            sharedStackProps: getSharedStackProps(accountName),
            tokenServiceStackProps: getTokenServiceStackProps(),
            icaEventPipeStackProps: getIcaEventPipeStackProps(),
          },
          statelessConfig: {
            postgresManagerStackProps: getPostgresManagerStackProps(),
            metadataManagerStackProps: getMetadataManagerStackProps(),
            sequenceRunManagerStackProps: getSequenceRunManagerStackProps(),
            fileManagerStackProps: getFileManagerStackProps(accountName),
            bsRunsUploadManagerStackProps: getBsRunsUploadManagerStackProps(accountName),
            icav2CopyBatchUtilityStackProps: getICAv2CopyBatchUtilityStackProps(accountName),
          },
        },
      };

    case 'prod':
      return {
        name: 'prod',
        region,
        accountId: accountIdAlias[accountName], // umccr_production
        stackProps: {
          statefulConfig: {
            sharedStackProps: getSharedStackProps(accountName),
            tokenServiceStackProps: getTokenServiceStackProps(),
            icaEventPipeStackProps: getIcaEventPipeStackProps(),
          },
          statelessConfig: {
            postgresManagerStackProps: getPostgresManagerStackProps(),
            metadataManagerStackProps: getMetadataManagerStackProps(),
            sequenceRunManagerStackProps: getSequenceRunManagerStackProps(),
            fileManagerStackProps: getFileManagerStackProps(accountName),
            bsRunsUploadManagerStackProps: getBsRunsUploadManagerStackProps(accountName),
            icav2CopyBatchUtilityStackProps: getICAv2CopyBatchUtilityStackProps(accountName),
          },
        },
      };
  }
};
