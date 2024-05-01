import {
  icav2AccessTokenSecretNameDev,
  icav2AccessTokenSecretNameStg,
  icav2AccessTokenSecretNameProd,
  AccountName,
  bsshFastqCopyManagerSfnName,
  bsshFastqCopyManagerSSMName,
  bsshFastqCopyManagerSSMArn,
  eventBusName,
} from '../constants';
import { BsshIcav2FastqCopyManagerConfig } from '../../lib/workload/stateless/stacks/bssh-icav2-fastq-copy-manager/deploy/stack';

export const getBsshIcav2FastqCopyManagerStackProps = (
  n: AccountName
): BsshIcav2FastqCopyManagerConfig => {
  const baseConfig = {
    Icav2CopyBatchUtilityStateMachineName: bsshFastqCopyManagerSfnName,
    BsshIcav2FastqCopyManagerStateMachineName: bsshFastqCopyManagerSfnName,
    BsshIcav2FastqCopyManagerStateMachineNameSsmParameterPath: bsshFastqCopyManagerSSMName,
    BsshIcav2FastqCopyManagerStateMachineArnSsmParameterPath: bsshFastqCopyManagerSSMArn,
    EventBusName: eventBusName,
  };

  switch (n) {
    case 'beta':
      return {
        ...baseConfig,
        Icav2JwtSecretsManagerPath: icav2AccessTokenSecretNameDev,
      };
    case 'gamma':
      return {
        ...baseConfig,
        Icav2JwtSecretsManagerPath: icav2AccessTokenSecretNameStg,
      };
    case 'prod':
      return {
        ...baseConfig,
        Icav2JwtSecretsManagerPath: icav2AccessTokenSecretNameProd,
      };
  }
};
