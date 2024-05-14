import {
  AppStage,
  icav2AccessTokenSecretName,
  bsshFastqCopyManagerSfnName,
  bsshFastqCopyManagerSSMName,
  bsshFastqCopyManagerSSMArn,
  eventBusName,
} from '../constants';
import { BsshIcav2FastqCopyManagerConfig } from '../../lib/workload/stateless/stacks/bssh-icav2-fastq-copy-manager/deploy/stack';

export const getBsshIcav2FastqCopyManagerStackProps = (
  stage: AppStage
): BsshIcav2FastqCopyManagerConfig => {
  return {
    icav2CopyBatchUtilityStateMachineName: bsshFastqCopyManagerSfnName,
    bsshIcav2FastqCopyManagerStateMachineName: bsshFastqCopyManagerSfnName,
    bsshIcav2FastqCopyManagerStateMachineNameSsmParameterPath: bsshFastqCopyManagerSSMName,
    bsshIcav2FastqCopyManagerStateMachineArnSsmParameterPath: bsshFastqCopyManagerSSMArn,
    eventBusName: eventBusName,
    icav2JwtSecretsManagerPath: icav2AccessTokenSecretName[stage],
  };
};
