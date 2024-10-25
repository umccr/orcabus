import {
  AppStage,
  eventBusName,
  sashBatchJobDefinitionArn,
  sashBatchJobQueueArn,
  sashEventDetailType,
  sashEventSource,
  sashNfDynamoDbTableSSMArn,
  sashNfDynamoDbTableSSMName,
  sashNfPipelineManagerDynamodbTableName,
  sashPipelineVersionSSMParameterPath,
  sashPipelineWorkflowType,
  sashPipelineWorkflowTypeVersion,
  sashReadyEventSource,
  sashServiceVersion,
  sashStateMachinePrefix,
} from '../constants';
import { SashNfPipelineManagerConfig } from '../../lib/workload/stateless/stacks/sash-pipeline-manager/deploy';
import { SashNfPipelineTableConfig } from '../../lib/workload/stateful/stacks/sash-dynamodb/deploy/stack';

// Stateful
export const getSashPipelineTableStackProps = (): SashNfPipelineTableConfig => {
  return {
    sashNfDynamodbTableArnSsmParameterPath: sashNfDynamoDbTableSSMArn,
    sashNfDynamodbTableNameSsmParameterPath: sashNfDynamoDbTableSSMName,
    dynamodbTableName: sashNfPipelineManagerDynamodbTableName,
  };
};

// Stateless
export const getSashPipelineManagerStackProps = (stage: AppStage): SashNfPipelineManagerConfig => {
  return {
    /* Table to store analysis metadata */
    dynamodbTableName: sashNfPipelineManagerDynamodbTableName,
    /* Internal and external buses */
    eventBusName: eventBusName,
    /* Event handling */
    workflowType: sashPipelineWorkflowType,
    workflowVersion: sashPipelineWorkflowTypeVersion,
    serviceVersion: sashServiceVersion,
    triggerLaunchSource: sashReadyEventSource,
    internalEventSource: sashEventSource,
    detailType: sashEventDetailType,
    /* AWS Batch things */
    batchJobQueueArn: sashBatchJobQueueArn[stage],
    batchJobDefinitionArn: sashBatchJobDefinitionArn[stage],
    /* Names for statemachines */
    stateMachinePrefix: sashStateMachinePrefix,
    /* SSM Workflow Parameters */
    pipelineVersionSsmPath: sashPipelineVersionSSMParameterPath,
  };
};
