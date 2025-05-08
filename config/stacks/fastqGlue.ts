import {
  AppStage,
  /* Secrets and ssms */
  jwtSecretName,
  hostedZoneNameParameterPath,
  /* S3 */
  icav2PipelineCacheBucket,
  icav2PipelineCachePrefix,
  /* Events */
  eventBusName,
  bsshFastqCopyManagerEventDetailType,
  fastqGlueEventsSource,
  fastqGlueEventsDetailType,
  bsshFastqCopyManagerWorkflowName,
  sequenceRunManagerEventDetailType,
  sequenceRunManagerEventSource,
} from '../constants';
import { FastqGlueStackConfig } from '../../lib/workload/stateless/stacks/fastq-glue/deploy/interfaces';

// Internal constants required for the stack
const metadataTrackingSheetIdSsmParameterPath = '/umccr/google/drive/tracking_sheet_id';
const gDriveAuthJsonSsmParameterPath = '/umccr/google/drive/lims_service_account_json';

// Stateless
export const getFastqGlueStackProps = (stage: AppStage): FastqGlueStackConfig => {
  return {
    /*
    Events stuff
    */
    eventBusName: eventBusName,

    // Input events
    workflowRunStateChangeEventDetailType: bsshFastqCopyManagerEventDetailType,
    workflowManagerEventSource: 'orcabus.workflowmanager',
    bsshFastqCopyManagerWorkflowName: bsshFastqCopyManagerWorkflowName,
    sequenceRunStateChangeEventDetailType: sequenceRunManagerEventDetailType,
    sequenceRunManageEventSource: sequenceRunManagerEventSource,

    // Output events
    eventDetailType: fastqGlueEventsDetailType,
    eventSource: fastqGlueEventsSource,

    /*
    Orcabus token and zone name for external lambda functions
    */
    orcabusTokenSecretsManagerPath: jwtSecretName,
    hostedZoneNameSsmParameterPath: hostedZoneNameParameterPath,

    /*
    Buckets stuff
    */
    pipelineCacheBucketName: icav2PipelineCacheBucket[stage],
    pipelineCachePrefix: icav2PipelineCachePrefix[stage],

    /*
    Topup / rerun workaround
    */
    gDriveAuthJsonSsmParameterPath: gDriveAuthJsonSsmParameterPath,
    metadataTrackingSheetIdSsmParameterPath: metadataTrackingSheetIdSsmParameterPath,
  };
};
