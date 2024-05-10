import {
  AppStage,
  eventBusName,
  cttsov2Icav2PipelineIdSSMParameterPath,
  icav2CopyBatchUtilityName,
  cttsov2Icav2PipelineManagerDynamodbTableName,
  icav2AccessTokenSecretName,
  cttsov2DynamoDbTableSSMArn,
  cttsov2DynamoDbTableSSMName,
  cttsov2Icav2PipelineWorkflowType,
  cttsov2Icav2ServiceVersion,
  cttsov2Icav2PipelineWorkflowTypeVersion,
  icaEventPipeStackName,
  cttsov2Icav2ReadyEventSource,
  cttsov2Icav2EventSource,
  cttsov2Icav2EventDetailType,
  cttsov2StateMachinePrefix,
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
    /* ICAv2 Pipeline analysis essentials */
    icav2TokenSecretId: icav2AccessTokenSecretName[stage], // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
    pipelineIdSsmPath: cttsov2Icav2PipelineIdSSMParameterPath, // List of parameters the workflow session state machine will need access to
    /* Table to store analyis metadata */
    dynamodbTableName: cttsov2Icav2PipelineManagerDynamodbTableName,
    /* Internal and external buses */
    eventBusName: eventBusName,
    icaEventPipeName: `${icaEventPipeStackName}Pipe`,
    /* Event handling */
    workflowType: cttsov2Icav2PipelineWorkflowType,
    workflowVersion: cttsov2Icav2PipelineWorkflowTypeVersion,
    serviceVersion: cttsov2Icav2ServiceVersion,
    triggerLaunchSource: cttsov2Icav2ReadyEventSource,
    internalEventSource: cttsov2Icav2EventSource,
    detailType: cttsov2Icav2EventDetailType,
    /* Names for statemachines */
    stateMachinePrefix: cttsov2StateMachinePrefix,
    /* Extras */
    icav2CopyBatchUtilityStateMachineName: icav2CopyBatchUtilityName,
  };
};
