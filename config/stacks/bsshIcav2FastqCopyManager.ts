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
    Icav2CopyBatchUtilityStateMachineName: bsshFastqCopyManagerSfnName,
    BsshIcav2FastqCopyManagerStateMachineName: bsshFastqCopyManagerSfnName,
    BsshIcav2FastqCopyManagerStateMachineNameSsmParameterPath: bsshFastqCopyManagerSSMName,
    BsshIcav2FastqCopyManagerStateMachineArnSsmParameterPath: bsshFastqCopyManagerSSMArn,
    EventBusName: eventBusName,
    Icav2JwtSecretsManagerPath: icav2AccessTokenSecretName[stage],
  };
};
