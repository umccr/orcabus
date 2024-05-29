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
import { getICAv2CopyBatchUtilityStackProps } from './stacks/icav2CopyBatchUtility';
import { getBsshIcav2FastqCopyManagerStackProps } from './stacks/bsshIcav2FastqCopyManager';
import {
  getCttsov2Icav2PipelineManagerStackProps,
  getCttsov2Icav2PipelineTableStackProps,
} from './stacks/cttsov2Icav2PipelineManager';
import { getEventSchemaStackProps } from './stacks/schema/events';
import { getDataSchemaStackProps } from './stacks/schema/data';
import {
  getBclConvertManagerTableStackProps,
  getBclConvertManagerStackProps,
} from './stacks/bclConvertManager';
import { getWorkflowManagerStackProps } from './stacks/workflowRunManager';

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
            cttsov2Icav2PipelineTableStackProps: getCttsov2Icav2PipelineTableStackProps(),
            BclConvertTableStackProps: getBclConvertManagerTableStackProps(stage),
          },
          statelessConfig: {
            postgresManagerStackProps: getPostgresManagerStackProps(),
            metadataManagerStackProps: getMetadataManagerStackProps(),
            sequenceRunManagerStackProps: getSequenceRunManagerStackProps(),
            fileManagerStackProps: getFileManagerStackProps(stage),
            bsRunsUploadManagerStackProps: getBsRunsUploadManagerStackProps(stage),
            icav2CopyBatchUtilityStackProps: getICAv2CopyBatchUtilityStackProps(stage),
            bsshIcav2FastqCopyManagerStackProps: getBsshIcav2FastqCopyManagerStackProps(stage),
            cttsov2Icav2PipelineManagerStackProps: getCttsov2Icav2PipelineManagerStackProps(stage),
            eventSchemaStackProps: getEventSchemaStackProps(),
            dataSchemaStackProps: getDataSchemaStackProps(),
            bclConvertManagerStackProps: getBclConvertManagerStackProps(stage),
            workflowManagerStackProps: getWorkflowManagerStackProps(),
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
            cttsov2Icav2PipelineTableStackProps: getCttsov2Icav2PipelineTableStackProps(),
            BclConvertTableStackProps: getBclConvertManagerTableStackProps(stage),
          },
          statelessConfig: {
            postgresManagerStackProps: getPostgresManagerStackProps(),
            metadataManagerStackProps: getMetadataManagerStackProps(),
            sequenceRunManagerStackProps: getSequenceRunManagerStackProps(),
            fileManagerStackProps: getFileManagerStackProps(stage),
            bsRunsUploadManagerStackProps: getBsRunsUploadManagerStackProps(stage),
            icav2CopyBatchUtilityStackProps: getICAv2CopyBatchUtilityStackProps(stage),
            bsshIcav2FastqCopyManagerStackProps: getBsshIcav2FastqCopyManagerStackProps(stage),
            cttsov2Icav2PipelineManagerStackProps: getCttsov2Icav2PipelineManagerStackProps(stage),
            eventSchemaStackProps: getEventSchemaStackProps(),
            dataSchemaStackProps: getDataSchemaStackProps(),
            bclConvertManagerStackProps: getBclConvertManagerStackProps(stage),
            workflowManagerStackProps: getWorkflowManagerStackProps(),
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
            cttsov2Icav2PipelineTableStackProps: getCttsov2Icav2PipelineTableStackProps(),
            BclConvertTableStackProps: getBclConvertManagerTableStackProps(stage),
          },
          statelessConfig: {
            postgresManagerStackProps: getPostgresManagerStackProps(),
            metadataManagerStackProps: getMetadataManagerStackProps(),
            sequenceRunManagerStackProps: getSequenceRunManagerStackProps(),
            fileManagerStackProps: getFileManagerStackProps(stage),
            bsRunsUploadManagerStackProps: getBsRunsUploadManagerStackProps(stage),
            icav2CopyBatchUtilityStackProps: getICAv2CopyBatchUtilityStackProps(stage),
            bsshIcav2FastqCopyManagerStackProps: getBsshIcav2FastqCopyManagerStackProps(stage),
            cttsov2Icav2PipelineManagerStackProps: getCttsov2Icav2PipelineManagerStackProps(stage),
            eventSchemaStackProps: getEventSchemaStackProps(),
            dataSchemaStackProps: getDataSchemaStackProps(),
            bclConvertManagerStackProps: getBclConvertManagerStackProps(stage),
            workflowManagerStackProps: getWorkflowManagerStackProps(),
          },
        },
      };
  }
};
