import {
  AppStage,
  eventBusName,
  icaEventPipeStackName,
  icav2AccessTokenSecretName,
  dragenIcav2ReferenceUriMappingSSMParameterPath,
  tnIcav2PipelineIdSSMParameterPath,
  tnIcav2PipelineManagerDynamodbTableName,
  tnIcav2PipelineWorkflowType,
  tnIcav2PipelineWorkflowTypeVersion,
  tnIcav2ServiceVersion,
  tnIcav2ReadyEventSource,
  tnIcav2EventSource,
  tnIcav2EventDetailType,
  tnStateMachinePrefix,
  tnDefaultReferenceVersion,
  tnDynamoDbTableSSMArn,
  tnDynamoDbTableSSMName,
} from '../constants';
import { TnIcav2PipelineManagerConfig } from '../../lib/workload/stateless/stacks/tumor-normal-pipeline-manager/deploy';
import { TnIcav2PipelineTableConfig } from '../../lib/workload/stateful/stacks/tumor-normal-pipeline-dynamo-db/deploy/stack';

// Stateful
export const getTnIcav2PipelineTableStackProps = (): TnIcav2PipelineTableConfig => {
  return {
    tnIcav2DynamodbTableArnSsmParameterPath: tnDynamoDbTableSSMArn,
    tnIcav2DynamodbTableNameSsmParameterPath: tnDynamoDbTableSSMName,
    dynamodbTableName: tnIcav2PipelineManagerDynamodbTableName,
  };
};

// Stateless
export const getTnIcav2PipelineManagerStackProps = (
  stage: AppStage
): TnIcav2PipelineManagerConfig => {
  return {
    /* ICAv2 Pipeline analysis essentials */
    icav2TokenSecretId: icav2AccessTokenSecretName[stage], // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
    pipelineIdSsmPath: tnIcav2PipelineIdSSMParameterPath, // List of parameters the workflow session state machine will need access to
    /* Table to store analyis metadata */
    dynamodbTableName: tnIcav2PipelineManagerDynamodbTableName,
    /* Internal and external buses */
    eventBusName: eventBusName,
    icaEventPipeName: `${icaEventPipeStackName}Pipe`,
    /* Event handling */
    workflowType: tnIcav2PipelineWorkflowType,
    workflowVersion: tnIcav2PipelineWorkflowTypeVersion,
    serviceVersion: tnIcav2ServiceVersion,
    triggerLaunchSource: tnIcav2ReadyEventSource,
    internalEventSource: tnIcav2EventSource,
    detailType: tnIcav2EventDetailType,
    /* Names for statemachines */
    stateMachinePrefix: tnStateMachinePrefix,
    /* SSM Workflow Parameters */
    defaultReferenceVersion: tnDefaultReferenceVersion,
    referenceUriSsmPath: dragenIcav2ReferenceUriMappingSSMParameterPath,
  };
};
