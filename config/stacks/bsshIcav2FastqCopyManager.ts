import {
  icav2AccessTokenSecretNameDev,
  icav2AccessTokenSecretNameStg,
  icav2AccessTokenSecretNameProd,
  AccountName,
  bsshFastqCopyManagerSfnName,
  bsshFastqCopyManagerSSMName,
  bsshFastqCopyManagerSSMArn,
} from '../constants';
import { BsshIcav2FastqCopyManagerConfig } from '../../lib/workload/stateless/stacks/bssh-icav2-fastq-copy-manager/deploy/stack';

export const getBsshIcav2FastqCopyManagerStackProps = (
  n: AccountName
): BsshIcav2FastqCopyManagerConfig => {
  const baseConfig = {
    icav2_copy_batch_utility_state_machine_name: bsshFastqCopyManagerSfnName,
    bssh_icav2_fastq_copy_manager_state_machine_name: bsshFastqCopyManagerSfnName,
    bssh_icav2_fastq_copy_manager_state_machine_name_ssm_parameter_path:
      bsshFastqCopyManagerSSMName,
    bssh_icav2_fastq_copy_manager_state_machine_arn_ssm_parameter_path: bsshFastqCopyManagerSSMArn,
  };

  switch (n) {
    case 'beta':
      return {
        ...baseConfig,
        icav2_jwt_secrets_manager_path: icav2AccessTokenSecretNameDev,
      };
    case 'gamma':
      return {
        ...baseConfig,
        icav2_jwt_secrets_manager_path: icav2AccessTokenSecretNameStg,
      };
    case 'prod':
      return {
        ...baseConfig,
        icav2_jwt_secrets_manager_path: icav2AccessTokenSecretNameProd,
      };
  }
};
