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
import { getEventSchemaStackProps } from './stacks/schema/events';
import { getDataSchemaStackProps } from './stacks/schema/data';
import {
  getBclConvertManagerTableStackProps,
  getBclConvertManagerStackProps,
} from './stacks/bclConvertManager';
import { getWorkflowManagerStackProps } from './stacks/workflowRunManager';
import {
  getBclconvertInteropQcIcav2PipelineManagerStackProps,
  getBclconvertInteropQcIcav2PipelineTableStackProps,
} from './stacks/bclconvertInteropQcIcav2PipelineManager';
import { getGlueStackProps, getStatefulGlueStackProps } from './stacks/stackyMcStackFace';

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
  const stackProps = {
    statefulConfig: {
      sharedStackProps: getSharedStackProps(stage),
      postgresManagerStackProps: getPostgresManagerStackProps(),
      tokenServiceStackProps: getTokenServiceStackProps(),
      icaEventPipeStackProps: getIcaEventPipeStackProps(),
      bclconvertInteropQcIcav2PipelineTableStackProps:
        getBclconvertInteropQcIcav2PipelineTableStackProps(),
      cttsov2Icav2PipelineTableStackProps: getCttsov2Icav2PipelineTableStackProps(),
      BclConvertTableStackProps: getBclConvertManagerTableStackProps(stage),
      stackyStatefulTablesStackProps: getStatefulGlueStackProps(),
    },
    statelessConfig: {
      metadataManagerStackProps: getMetadataManagerStackProps(stage),
      sequenceRunManagerStackProps: getSequenceRunManagerStackProps(stage),
      fileManagerStackProps: getFileManagerStackProps(stage),
      bsRunsUploadManagerStackProps: getBsRunsUploadManagerStackProps(stage),
      bsshIcav2FastqCopyManagerStackProps: getBsshIcav2FastqCopyManagerStackProps(stage),
      bclconvertInteropQcIcav2PipelineManagerStackProps:
        getBclconvertInteropQcIcav2PipelineManagerStackProps(stage),
      cttsov2Icav2PipelineManagerStackProps: getCttsov2Icav2PipelineManagerStackProps(stage),
      eventSchemaStackProps: getEventSchemaStackProps(),
      dataSchemaStackProps: getDataSchemaStackProps(),
      bclConvertManagerStackProps: getBclConvertManagerStackProps(stage),
      workflowManagerStackProps: getWorkflowManagerStackProps(stage),
      stackyMcStackFaceProps: getGlueStackProps(),
    },
  };

  switch (stage) {
    case AppStage.BETA:
      return {
        name: 'beta',
        region,
        accountId: accountIdAlias[stage], // umccr_development
        stackProps: stackProps,
      };

    case AppStage.GAMMA:
      return {
        name: 'gamma',
        region,
        accountId: accountIdAlias[stage], // umccr_staging
        stackProps: stackProps,
      };

    case AppStage.PROD:
      return {
        name: 'prod',
        region,
        accountId: accountIdAlias[stage], // umccr_production
        stackProps: stackProps,
      };
  }
};
