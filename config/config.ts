import { region, AppStage, accountIdAlias } from './constants';
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
import { getBsshIcav2FastqCopyManagerStackProps } from './stacks/bsshIcav2FastqCopyManager';
import {
  getCttsov2Icav2PipelineManagerStackProps,
  getCttsov2Icav2PipelineTableStackProps,
} from './stacks/cttsov2Icav2PipelineManager';
import { getSchemaStackProps } from './stacks/schema';
import {
  getIcav2EventTranslatorTableStackProps,
  getIcav2EventTranslatorStackProps,
} from './stacks/icav2EventTranslator';
import {
  getBclconvertInteropQcIcav2PipelineManagerStackProps,
  getBclconvertInteropQcIcav2PipelineTableStackProps,
} from './stacks/bclconvertInteropQcIcav2PipelineManager';

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
 * @param stage the name of account stage
 * @returns the configuration for the given app stage
 */
export const getEnvironmentConfig = (stage: AppStage): EnvironmentConfig | null => {
  switch (stage) {
    case AppStage.BETA:
      return {
        name: 'beta',
        region,
        accountId: accountIdAlias[stage], // umccr_development
        stackProps: {
          statefulConfig: {
            sharedStackProps: getSharedStackProps(stage),
            tokenServiceStackProps: getTokenServiceStackProps(),
            icaEventPipeStackProps: getIcaEventPipeStackProps(),
            bclconvertInteropQcIcav2PipelineTableStackProps:
              getBclconvertInteropQcIcav2PipelineTableStackProps(),
            cttsov2Icav2PipelineTableStackProps: getCttsov2Icav2PipelineTableStackProps(),
            icav2EventTranslatorTableStackProps: getIcav2EventTranslatorTableStackProps(stage),
          },
          statelessConfig: {
            postgresManagerStackProps: getPostgresManagerStackProps(),
            metadataManagerStackProps: getMetadataManagerStackProps(),
            sequenceRunManagerStackProps: getSequenceRunManagerStackProps(),
            fileManagerStackProps: getFileManagerStackProps(stage),
            bsRunsUploadManagerStackProps: getBsRunsUploadManagerStackProps(stage),
            bsshIcav2FastqCopyManagerStackProps: getBsshIcav2FastqCopyManagerStackProps(stage),
            bclconvertInteropQcIcav2PipelineManagerStackProps:
              getBclconvertInteropQcIcav2PipelineManagerStackProps(stage),
            cttsov2Icav2PipelineManagerStackProps: getCttsov2Icav2PipelineManagerStackProps(stage),
            schemaStackProps: getSchemaStackProps(),
            icav2EventTranslatorStackProps: getIcav2EventTranslatorStackProps(),
          },
        },
      };

    case AppStage.GAMMA:
      return {
        name: 'gamma',
        region,
        accountId: accountIdAlias[stage], // umccr_staging
        stackProps: {
          statefulConfig: {
            sharedStackProps: getSharedStackProps(stage),
            tokenServiceStackProps: getTokenServiceStackProps(),
            icaEventPipeStackProps: getIcaEventPipeStackProps(),
            bclconvertInteropQcIcav2PipelineTableStackProps:
              getBclconvertInteropQcIcav2PipelineTableStackProps(),
            cttsov2Icav2PipelineTableStackProps: getCttsov2Icav2PipelineTableStackProps(),
            icav2EventTranslatorTableStackProps: getIcav2EventTranslatorTableStackProps(stage),
          },
          statelessConfig: {
            postgresManagerStackProps: getPostgresManagerStackProps(),
            metadataManagerStackProps: getMetadataManagerStackProps(),
            sequenceRunManagerStackProps: getSequenceRunManagerStackProps(),
            fileManagerStackProps: getFileManagerStackProps(stage),
            bsRunsUploadManagerStackProps: getBsRunsUploadManagerStackProps(stage),
            bsshIcav2FastqCopyManagerStackProps: getBsshIcav2FastqCopyManagerStackProps(stage),
            bclconvertInteropQcIcav2PipelineManagerStackProps:
              getBclconvertInteropQcIcav2PipelineManagerStackProps(stage),
            cttsov2Icav2PipelineManagerStackProps: getCttsov2Icav2PipelineManagerStackProps(stage),
            schemaStackProps: getSchemaStackProps(),
            icav2EventTranslatorStackProps: getIcav2EventTranslatorStackProps(),
          },
        },
      };

    case AppStage.PROD:
      return {
        name: 'prod',
        region,
        accountId: accountIdAlias[stage], // umccr_production
        stackProps: {
          statefulConfig: {
            sharedStackProps: getSharedStackProps(stage),
            tokenServiceStackProps: getTokenServiceStackProps(),
            icaEventPipeStackProps: getIcaEventPipeStackProps(),
            bclconvertInteropQcIcav2PipelineTableStackProps:
              getBclconvertInteropQcIcav2PipelineTableStackProps(),
            cttsov2Icav2PipelineTableStackProps: getCttsov2Icav2PipelineTableStackProps(),
            icav2EventTranslatorTableStackProps: getIcav2EventTranslatorTableStackProps(stage),
          },
          statelessConfig: {
            postgresManagerStackProps: getPostgresManagerStackProps(),
            metadataManagerStackProps: getMetadataManagerStackProps(),
            sequenceRunManagerStackProps: getSequenceRunManagerStackProps(),
            fileManagerStackProps: getFileManagerStackProps(stage),
            bsRunsUploadManagerStackProps: getBsRunsUploadManagerStackProps(stage),
            bsshIcav2FastqCopyManagerStackProps: getBsshIcav2FastqCopyManagerStackProps(stage),
            bclconvertInteropQcIcav2PipelineManagerStackProps:
              getBclconvertInteropQcIcav2PipelineManagerStackProps(stage),
            cttsov2Icav2PipelineManagerStackProps: getCttsov2Icav2PipelineManagerStackProps(stage),
            schemaStackProps: getSchemaStackProps(),
            icav2EventTranslatorStackProps: getIcav2EventTranslatorStackProps(),
          },
        },
      };
  }
};
