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
    Icav2CopyBatchStateMachineName: icav2CopyBatchUtilityName,
    Icav2CopyBatchStateMachineArnSsmParameterPath: icav2CopyBatchSSMBatchArn,
    Icav2CopyBatchStateMachineNameSsmParameterPath: icav2CopyBatchSSMBatchName,
    Icav2CopySingleStateMachineName: icav2CopySingleUtilityName,
    Icav2CopySingleStateMachineArnSsmParameterPath: icav2CopyBatchSSMSingleArn,
    Icav2CopySingleStateMachineNameSsmParameterPath: icav2CopyBatchSSMSingleName,
    Icav2TokenSecretId: icav2AccessTokenSecretName[stage],
  };
};
