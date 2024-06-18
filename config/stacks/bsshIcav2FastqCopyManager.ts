import {
  AppStage,
  icav2AccessTokenSecretName,
  eventBusName,
  bsshFastqCopyManagerWorkflowName,
  bsshFastqCopyManagerWorkflowTypeVersion,
  bsshFastqCopyManagerServiceVersion,
  bsshFastqCopyManagerReadyEventSource,
  bsshFastqCopyManagerEventSource,
  bsshFastqCopyManagerEventDetailType,
} from '../constants';
import { BsshIcav2FastqCopyManagerConfig } from '../../lib/workload/stateless/stacks/bssh-icav2-fastq-copy-manager/deploy/stack';

export const getBsshIcav2FastqCopyManagerStackProps = (
  stage: AppStage
): BsshIcav2FastqCopyManagerConfig => {
  return {
    detailType: bsshFastqCopyManagerEventDetailType,
    icav2TokenSecretId: icav2AccessTokenSecretName[stage],
    internalEventSource: bsshFastqCopyManagerEventSource,
    serviceVersion: bsshFastqCopyManagerServiceVersion,
    triggerLaunchSource: bsshFastqCopyManagerReadyEventSource,
    workflowName: bsshFastqCopyManagerWorkflowName,
    workflowVersion: bsshFastqCopyManagerWorkflowTypeVersion,
    eventBusName: eventBusName,
  };
};
