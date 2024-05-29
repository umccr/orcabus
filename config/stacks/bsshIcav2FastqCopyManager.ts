import {
  AppStage,
  icav2AccessTokenSecretName,
  bsshFastqCopyManagerSfnPrefix,
  eventBusName,
  bsshFastqCopyManagerWorkflowType,
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
    icav2CopyBatchUtilityStateMachineName: bsshFastqCopyManagerSfnName,
    eventBusName: eventBusName,
  };
};
