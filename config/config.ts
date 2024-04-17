import { region } from './constants';
import { StatefulStackCollectionProps } from '../lib/workload/stateful/statefulStackCollectionClass';
import { StatelessStackCollectionProps } from '../lib/workload/stateless/statelessStackCollectionClass';
import { getSharedStackProps } from './stacks/shared';
import { getIcaEventPipeStackProps } from './stacks/icaEventPipe';
import { getTokenServiceStackProps } from './stacks/tokenService';
import { getPostgresManagerStackProps } from './stacks/postgresManager';
import { getMetadataManagerStackProps } from './stacks/metadataManager';
import { getSequenceRunManagerStackProps } from './stacks/sequenceRunManager';
import { getFileManagerStackProps } from './stacks/fileManager';

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
  let config = null;
  switch (accountName) {
    case 'beta':
      config = {
        name: 'beta',
        region,
        accountId: '843407916570', // umccr_development
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
          },
        },
      };
      break;

    case 'gamma':
      config = {
        name: 'gamma',
        region,
        accountId: '455634345446', // umccr_staging
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
          },
        },
      };
      break;

    case 'prod':
      config = {
        name: 'prod',
        region,
        accountId: '472057503814', // umccr_production
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
          },
        },
      };
      break;
  }

  return config;
};
