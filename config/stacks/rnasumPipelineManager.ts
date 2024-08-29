import {
  AppStage,
  eventBusName,
  icaEventPipeStackName,
  icav2AccessTokenSecretName,
  dragenIcav2ReferenceUriMappingSSMParameterPath,
  rnasumIcav2PipelineIdSSMParameterPath,
  rnasumIcav2PipelineManagerDynamodbTableName,
  rnasumIcav2PipelineWorkflowType,
  rnasumIcav2PipelineWorkflowTypeVersion,
  rnasumIcav2ServiceVersion,
  rnasumIcav2ReadyEventSource,
  rnasumIcav2EventSource,
  rnasumIcav2EventDetailType,
  rnasumStateMachinePrefix,
  rnasumDynamoDbTableSSMArn,
  rnasumDynamoDbTableSSMName,
  rnasumDefaultDatasetVersion,
} from '../constants';
import { RnasumIcav2PipelineManagerConfig } from '../../lib/workload/stateless/stacks/rnasum-pipeline-manager/deploy';
import { RnasumIcav2PipelineTableConfig } from '../../lib/workload/stateful/stacks/rnasum-pipeline-dynamo-db/deploy/stack';

// Stateful
export const getRnasumIcav2PipelineTableStackProps = (): RnasumIcav2PipelineTableConfig => {
  return {
    rnasumIcav2DynamodbTableArnSsmParameterPath: rnasumDynamoDbTableSSMArn,
    rnasumIcav2DynamodbTableNameSsmParameterPath: rnasumDynamoDbTableSSMName,
    dynamodbTableName: rnasumIcav2PipelineManagerDynamodbTableName,
  };
};

// Stateless
export const getRnasumIcav2PipelineManagerStackProps = (
  stage: AppStage
): RnasumIcav2PipelineManagerConfig => {
  return {
    /* ICAv2 Pipeline analysis essentials */
    icav2TokenSecretId: icav2AccessTokenSecretName[stage], // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
    pipelineIdSsmPath: rnasumIcav2PipelineIdSSMParameterPath, // List of parameters the workflow session state machine will need access to
    /* Table to store analyis metadata */
    dynamodbTableName: rnasumIcav2PipelineManagerDynamodbTableName,
    /* Internal and external buses */
    eventBusName: eventBusName,
    icaEventPipeName: `${icaEventPipeStackName}Pipe`,
    /* Event handling */
    workflowType: rnasumIcav2PipelineWorkflowType,
    workflowVersion: rnasumIcav2PipelineWorkflowTypeVersion,
    serviceVersion: rnasumIcav2ServiceVersion,
    triggerLaunchSource: rnasumIcav2ReadyEventSource,
    internalEventSource: rnasumIcav2EventSource,
    detailType: rnasumIcav2EventDetailType,
    /* Names for statemachines */
    stateMachinePrefix: rnasumStateMachinePrefix,
    /* Standard Parameters */
    defaultDatasetVersion: rnasumDefaultDatasetVersion,
  };
};
