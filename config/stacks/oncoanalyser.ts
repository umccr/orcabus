import {
  AppStage,
  eventBusName,
  oncoanalyserBatchJobDefinitionArn,
  oncoanalyserBatchJobQueueArn,
  oncoanalyserEventDetailType,
  oncoanalyserEventSource,
  oncoanalyserNfDynamoDbTableSSMArn,
  oncoanalyserNfDynamoDbTableSSMName,
  oncoanalyserNfPipelineManagerDynamodbTableName,
  oncoanalyserPipelineVersionSSMParameterPath,
  oncoanalyserPipelineWorkflowTypePrefix,
  oncoanalyserPipelineWorkflowTypeVersion,
  oncoanalyserReadyEventSource,
  oncoanalyserServiceVersion,
  oncoanalyserStateMachinePrefix,
} from '../constants';
import { OncoanalyserNfPipelineManagerConfig } from '../../lib/workload/stateless/stacks/oncoanalyser-pipeline-manager/deploy';
import { OncoanalyserNfPipelineTableConfig } from '../../lib/workload/stateful/stacks/oncoanalyser-dynamodb/deploy/stack';

// Stateful
export const getOncoanalyserPipelineTableStackProps = (): OncoanalyserNfPipelineTableConfig => {
  return {
    oncoanalyserNfDynamodbTableArnSsmParameterPath: oncoanalyserNfDynamoDbTableSSMArn,
    oncoanalyserNfDynamodbTableNameSsmParameterPath: oncoanalyserNfDynamoDbTableSSMName,
    dynamodbTableName: oncoanalyserNfPipelineManagerDynamodbTableName,
  };
};

// Stateless
export const getOncoanalyserPipelineManagerStackProps = (
  stage: AppStage
): OncoanalyserNfPipelineManagerConfig => {
  return {
    /* Table to store analysis metadata */
    dynamodbTableName: oncoanalyserNfPipelineManagerDynamodbTableName,
    /* Internal and external buses */
    eventBusName: eventBusName,
    /* Event handling */
    workflowTypePrefix: oncoanalyserPipelineWorkflowTypePrefix,
    workflowVersion: oncoanalyserPipelineWorkflowTypeVersion,
    serviceVersion: oncoanalyserServiceVersion,
    triggerLaunchSource: oncoanalyserReadyEventSource,
    internalEventSource: oncoanalyserEventSource,
    detailType: oncoanalyserEventDetailType,
    /* AWS Batch things */
    batchJobQueueArn: oncoanalyserBatchJobQueueArn[stage],
    batchJobDefinitionArn: oncoanalyserBatchJobDefinitionArn[stage],
    /* Names for statemachines */
    stateMachinePrefix: oncoanalyserStateMachinePrefix,
    /* SSM Workflow Parameters */
    pipelineVersionSsmPath: oncoanalyserPipelineVersionSSMParameterPath,
  };
};
