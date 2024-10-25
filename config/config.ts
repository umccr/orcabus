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
import { getDataBucketStackProps } from './stacks/dataBucket';
import {
  getWgtsQcIcav2PipelineManagerStackProps,
  getWgtsQcIcav2PipelineTableStackProps,
} from './stacks/wgtsQcPipelineManager';
import {
  getTnIcav2PipelineManagerStackProps,
  getTnIcav2PipelineTableStackProps,
} from './stacks/tumorNormalPipelineManager';
import {
  getWtsIcav2PipelineManagerStackProps,
  getWtsIcav2PipelineTableStackProps,
} from './stacks/wtsPipelineManager';
import {
  getUmccriseIcav2PipelineManagerStackProps,
  getUmccriseIcav2PipelineTableStackProps,
} from './stacks/umccrisePipelineManager';
import {
  getRnasumIcav2PipelineManagerStackProps,
  getRnasumIcav2PipelineTableStackProps,
} from './stacks/rnasumPipelineManager';
import { getFmAnnotatorProps } from './stacks/fmAnnotator';
import {
  getPierianDxPipelineManagerStackProps,
  getPierianDxPipelineTableStackProps,
} from './stacks/pierianDxPipelineManager';
import { getAuthorizationManagerStackProps } from './stacks/authorizationManager';

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
      authorizationManagerStackProps: getAuthorizationManagerStackProps(stage),
      dataBucketStackProps: getDataBucketStackProps(stage),
      sharedStackProps: getSharedStackProps(stage),
      postgresManagerStackProps: getPostgresManagerStackProps(),
      tokenServiceStackProps: getTokenServiceStackProps(),
      icaEventPipeStackProps: getIcaEventPipeStackProps(),
      bclconvertInteropQcIcav2PipelineTableStackProps:
        getBclconvertInteropQcIcav2PipelineTableStackProps(),
      cttsov2Icav2PipelineTableStackProps: getCttsov2Icav2PipelineTableStackProps(),
      wgtsQcIcav2PipelineTableStackProps: getWgtsQcIcav2PipelineTableStackProps(),
      tnIcav2PipelineTableStackProps: getTnIcav2PipelineTableStackProps(),
      wtsIcav2PipelineTableStackProps: getWtsIcav2PipelineTableStackProps(),
      umccriseIcav2PipelineTableStackProps: getUmccriseIcav2PipelineTableStackProps(),
      rnasumIcav2PipelineTableStackProps: getRnasumIcav2PipelineTableStackProps(),
      BclConvertTableStackProps: getBclConvertManagerTableStackProps(stage),
      stackyStatefulTablesStackProps: getStatefulGlueStackProps(),
      pierianDxPipelineTableStackProps: getPierianDxPipelineTableStackProps(),
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
      wgtsQcIcav2PipelineManagerStackProps: getWgtsQcIcav2PipelineManagerStackProps(stage),
      tnIcav2PipelineManagerStackProps: getTnIcav2PipelineManagerStackProps(stage),
      wtsIcav2PipelineManagerStackProps: getWtsIcav2PipelineManagerStackProps(stage),
      umccriseIcav2PipelineManagerStackProps: getUmccriseIcav2PipelineManagerStackProps(stage),
      rnasumIcav2PipelineManagerStackProps: getRnasumIcav2PipelineManagerStackProps(stage),
      pieriandxPipelineManagerStackProps: getPierianDxPipelineManagerStackProps(stage),
      eventSchemaStackProps: getEventSchemaStackProps(),
      dataSchemaStackProps: getDataSchemaStackProps(),
      bclConvertManagerStackProps: getBclConvertManagerStackProps(stage),
      workflowManagerStackProps: getWorkflowManagerStackProps(stage),
      stackyMcStackFaceProps: getGlueStackProps(stage),
      fmAnnotatorProps: getFmAnnotatorProps(),
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
