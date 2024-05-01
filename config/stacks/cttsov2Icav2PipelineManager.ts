import {
  AppStage,
  eventBusName,
  cttsov2Icav2PipelineIdSSMParameterPath,
  icav2CopyBatchUtilityName,
  cttsov2Icav2PipelineSfnSSMName,
  cttsov2Icav2PipelineSfnSSMArn,
  cttsov2Icav2PipelineManagerDynamodbTableName,
  icav2AccessTokenSecretName,
  cttsov2DynamoDbTableSSMArn,
  cttsov2DynamoDbTableSSMName,
} from '../constants';
import { Cttsov2Icav2PipelineManagerConfig } from '../../lib/workload/stateless/stacks/cttso-v2-pipeline-manager/deploy/stack';
import { Cttsov2Icav2PipelineTableConfig } from '../../lib/workload/stateful/stacks/cttso-v2-pipeline-dynamo-db/deploy/stack';

// Stateful
export const getCttsov2Icav2PipelineTableStackProps = (): Cttsov2Icav2PipelineTableConfig => {
  return {
    cttsov2Icav2DynamodbTableArnSsmParameterPath: cttsov2DynamoDbTableSSMArn,
    cttsov2Icav2DynamodbTableNameSsmParameterPath: cttsov2DynamoDbTableSSMName,
    dynamodbTableName: cttsov2Icav2PipelineManagerDynamodbTableName,
  };
};

// Stateless
export const getCttsov2Icav2PipelineManagerStackProps = (
  stage: AppStage
): Cttsov2Icav2PipelineManagerConfig => {
  return {
    pipelineIdSsmPath: cttsov2Icav2PipelineIdSSMParameterPath,
    icav2CopyBatchUtilityStateMachineName: icav2CopyBatchUtilityName,
    cttsov2LaunchStateMachineArnSsmParameterPath: cttsov2Icav2PipelineSfnSSMArn,
    cttsov2LaunchStateMachineNameSsmParameterPath: cttsov2Icav2PipelineSfnSSMName,
    dynamodbTableName: cttsov2Icav2PipelineManagerDynamodbTableName,
    eventbusName: eventBusName,
    icav2TokenSecretId: icav2AccessTokenSecretName[stage],
  };
};
