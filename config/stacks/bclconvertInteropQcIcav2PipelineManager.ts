import {
  AppStage,
  eventBusName,
  bclconvertInteropQcIcav2PipelineIdSSMParameterPath,
  bclconvertInteropQcIcav2PipelineManagerDynamodbTableName,
  icav2AccessTokenSecretName,
  bclconvertInteropQcDynamoDbTableSSMArn,
  bclconvertInteropQcDynamoDbTableSSMName,
  bclconvertInteropQcIcav2PipelineWorkflowType,
  bclconvertInteropQcIcav2ServiceVersion,
  bclconvertInteropQcIcav2PipelineWorkflowTypeVersion,
  bclconvertInteropQcIcav2EventSource,
  bclconvertInteropQcIcav2EventDetailType,
  bclconvertInteropQcStateMachinePrefix,
  bclconvertInteropQcIcav2ReadyEventSource,
  icaEventPipeStackName,
} from '../constants';
import { BclconvertInteropQcIcav2PipelineManagerConfig } from '../../lib/workload/stateless/stacks/bclconvert-interop-qc-pipeline-manager/deploy/stack';
import { BclconvertInteropQcIcav2PipelineTableConfig } from '../../lib/workload/stateful/stacks/bclconvert-interop-qc-pipeline-dynamo-db/deploy/stack';

// Stateful
export const getBclconvertInteropQcIcav2PipelineTableStackProps =
  (): BclconvertInteropQcIcav2PipelineTableConfig => {
    return {
      bclconvertInteropQcIcav2DynamodbTableArnSsmParameterPath:
        bclconvertInteropQcDynamoDbTableSSMArn,
      bclconvertInteropQcIcav2DynamodbTableNameSsmParameterPath:
        bclconvertInteropQcDynamoDbTableSSMName,
      dynamodbTableName: bclconvertInteropQcIcav2PipelineManagerDynamodbTableName,
    };
  };

// Stateless
export const getBclconvertInteropQcIcav2PipelineManagerStackProps = (
  stage: AppStage
): BclconvertInteropQcIcav2PipelineManagerConfig => {
  return {
    /* ICAv2 Configurations */
    icav2TokenSecretId: icav2AccessTokenSecretName[stage],
    pipelineIdSsmPath: bclconvertInteropQcIcav2PipelineIdSSMParameterPath,
    /* Stateful names */
    dynamodbTableName: bclconvertInteropQcIcav2PipelineManagerDynamodbTableName,
    eventBusName: eventBusName,
    icaEventPipeName: `${icaEventPipeStackName}Pipe`,
    /* Event configurations */
    workflowType: bclconvertInteropQcIcav2PipelineWorkflowType,
    workflowVersion: bclconvertInteropQcIcav2PipelineWorkflowTypeVersion,
    serviceVersion: bclconvertInteropQcIcav2ServiceVersion,
    triggerLaunchSource: bclconvertInteropQcIcav2ReadyEventSource,
    internalEventSource: bclconvertInteropQcIcav2EventSource,
    detailType: bclconvertInteropQcIcav2EventDetailType,
    /*
    Names for statemachines
    */
    stateMachinePrefix: bclconvertInteropQcStateMachinePrefix,
  };
};
