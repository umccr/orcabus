import {
  AppStage,
  icav2AccessTokenSecretName,
  icav2CopyBatchUtilityName,
  icav2CopyBatchSSMBatchArn,
  icav2CopySingleUtilityName,
  icav2CopyBatchSSMBatchName,
  icav2CopyBatchSSMSingleArn,
  icav2CopyBatchSSMSingleName,
} from '../constants';

import { ICAv2CopyBatchUtilityConfig } from '../../lib/workload/stateless/stacks/icav2-copy-batch-utility/deploy/stack';

export const getICAv2CopyBatchUtilityStackProps = (
  stage: AppStage
): ICAv2CopyBatchUtilityConfig => {
  return {
    icav2_copy_batch_state_machine_name: icav2CopyBatchUtilityName,
    icav2_copy_batch_state_machine_arn_ssm_parameter_path: icav2CopyBatchSSMBatchArn,
    icav2_copy_batch_state_machine_name_ssm_parameter_path: icav2CopyBatchSSMBatchName,
    icav2_copy_single_state_machine_name: icav2CopySingleUtilityName,
    icav2_copy_single_state_machine_arn_ssm_parameter_path: icav2CopyBatchSSMSingleArn,
    icav2_copy_single_state_machine_name_ssm_parameter_path: icav2CopyBatchSSMSingleName,
    icav2_token_secret_id: icav2AccessTokenSecretName[stage],
  };
};
