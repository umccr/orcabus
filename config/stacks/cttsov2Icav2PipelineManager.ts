import {
  AccountName,
  eventBusName,
  cttsov2Icav2PipelineIdSSMParameterPath,
  icav2CopyBatchUtilityName,
  cttsov2Icav2PipelineSfnSSMName,
  cttsov2Icav2PipelineSfnSSMArn,
  cttsov2Icav2PipelineManagerDynamodbTableName,
  icav2AccessTokenSecretNameDev,
  icav2AccessTokenSecretNameStg,
  icav2AccessTokenSecretNameProd,
  cttsov2DynamoDbTableSSMArn,
  cttsov2DynamoDbTableSSMName,
} from '../constants';
import { Cttsov2Icav2PipelineManagerConfig } from '../../lib/workload/stateless/stacks/cttso-v2-pipeline-manager/deploy/stack';
import { Cttsov2Icav2PipelineTableConfig } from '../../lib/workload/stateful/stacks/cttso-v2-pipeline-dynamo-db/deploy/stack';

// Stateful
export const getCttsov2Icav2PipelineTableStackProps = (): Cttsov2Icav2PipelineTableConfig => {
  return {
    cttsov2_icav2_dynamodb_table_arn_ssm_parameter_path: cttsov2DynamoDbTableSSMArn,
    cttsov2_icav2_dynamodb_table_name_ssm_parameter_path: cttsov2DynamoDbTableSSMName,
    dynamodb_table_name: cttsov2Icav2PipelineManagerDynamodbTableName,
  };
};

// Stateless
export const getCttsov2Icav2PipelineManagerStackProps = (
  n: AccountName
): Cttsov2Icav2PipelineManagerConfig => {
  const baseConfig = {
    ssm_parameter_list: [cttsov2Icav2PipelineIdSSMParameterPath],
    icav2_copy_batch_utility_state_machine_name: icav2CopyBatchUtilityName,
    cttso_v2_launch_state_machine_arn_ssm_parameter_path: cttsov2Icav2PipelineSfnSSMArn,
    cttso_v2_launch_state_machine_name_ssm_parameter_path: cttsov2Icav2PipelineSfnSSMName,
    dynamodb_table_name: cttsov2Icav2PipelineManagerDynamodbTableName,
    eventbus_name: eventBusName,
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
