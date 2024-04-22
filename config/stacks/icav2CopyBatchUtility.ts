import {
  icav2AccessTokenSecretNameDev,
  icav2AccessTokenSecretNameStg,
  icav2AccessTokenSecretNameProd,
  AccountName,
  icav2CopyBatchSSMRoot,
} from '../constants';

import { ICAv2CopyBatchUtilityConfig } from '../../lib/workload/stateless/stacks/icav2-copy-batch-utility/deploy/stack';
import path from 'path';

export const getICAv2CopyBatchUtilityStackProps = (n: AccountName): ICAv2CopyBatchUtilityConfig => {
  const baseConfig = {
    icav2_copy_batch_state_machine_name: 'icav2_copy_batch_utility_sfn',
    icav2_copy_batch_state_machine_arn_ssm_parameter_path: path.join(
      icav2CopyBatchSSMRoot,
      'batch_sfn_arn'
    ),
    icav2_copy_batch_state_machine_name_ssm_parameter_path: path.join(
      icav2CopyBatchSSMRoot,
      'batch_sfn_name'
    ),
    icav2_copy_single_state_machine_name: 'icav2_single_batch_utility_sfn',
    icav2_copy_single_state_machine_arn_ssm_parameter_path: path.join(
      icav2CopyBatchSSMRoot,
      'single_sfn_arn'
    ),
    icav2_copy_single_state_machine_name_ssm_parameter_path: path.join(
      icav2CopyBatchSSMRoot,
      'single_sfn_name'
    ),
  };

  switch (n) {
    case 'beta':
      return {
        ...baseConfig,
        icav2_token_secret_id: icav2AccessTokenSecretNameDev,
      };
    case 'gamma':
      return {
        ...baseConfig,
        icav2_token_secret_id: icav2AccessTokenSecretNameStg,
      };
    case 'prod':
      return {
        ...baseConfig,
        icav2_token_secret_id: icav2AccessTokenSecretNameProd,
      };
  }
};
