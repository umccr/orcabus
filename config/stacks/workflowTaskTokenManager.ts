import { AppStage, eventBusName, workflowTaskTokenManagerDynamodbTableName } from '../constants';
import { WorkflowTaskTokenManagerConfig } from '../../lib/workload/stateless/stacks/workflow-task-token-manager/deploy';
import { WorkflowTaskTokenTableConfig } from '../../lib/workload/stateful/stacks/workflow-task-token-manager-dynamo-db/deploy';

// Stateful
export const getWorkflowTaskTokenManagerTableStackProps = (): WorkflowTaskTokenTableConfig => {
  return {
    dynamodbTableName: workflowTaskTokenManagerDynamodbTableName,
  };
};

// Stateless
export const getWorkflowTaskTokenManagerStackProps = (): WorkflowTaskTokenManagerConfig => {
  return {
    dynamodbTableName: workflowTaskTokenManagerDynamodbTableName,
    eventBusName: eventBusName,
    stateMachinePrefix: 'workflow-task-token',
  };
};
