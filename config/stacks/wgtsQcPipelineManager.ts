import {
  AppStage,
  eventBusName,
  wgtsQcIcav2PipelineIdSSMParameterPath,
  wgtsQcIcav2PipelineManagerDynamodbTableName,
  icav2AccessTokenSecretName,
  wgtsQcDynamoDbTableSSMArn,
  wgtsQcDynamoDbTableSSMName,
  wgtsQcIcav2PipelineWorkflowType,
  wgtsQcIcav2ServiceVersion,
  wgtsQcIcav2PipelineWorkflowTypeVersion,
  icaEventPipeStackName,
  wgtsQcIcav2ReadyEventSource,
  wgtsQcIcav2EventSource,
  wgtsQcIcav2EventDetailType,
  wgtsQcStateMachinePrefix,
  wgtsQcIcav2AnnotationUriMappingSSMParameterPath,
  wgtsQcIcav2ReferenceUriMappingSSMParameterPath,
  wgtsQcDefaultReferenceVersion,
  wgtsQcDefaultAnnotationVersion,
} from '../constants';
import { WgtsQcIcav2PipelineTableConfig } from '../../lib/workload/stateful/stacks/wgtsqc-pipeline-dynamo-db/deploy/stack';
import { WgtsQcIcav2PipelineManagerConfig } from '../../lib/workload/stateless/stacks/wgts-alignment-qc-pipeline-manager/deploy';

// Stateful
export const getWgtsQcIcav2PipelineTableStackProps = (): WgtsQcIcav2PipelineTableConfig => {
  return {
    wgtsQcIcav2DynamodbTableArnSsmParameterPath: wgtsQcDynamoDbTableSSMArn,
    wgtsQcIcav2DynamodbTableNameSsmParameterPath: wgtsQcDynamoDbTableSSMName,
    dynamodbTableName: wgtsQcIcav2PipelineManagerDynamodbTableName,
  };
};

// Stateless
export const getWgtsQcIcav2PipelineManagerStackProps = (
  stage: AppStage
): WgtsQcIcav2PipelineManagerConfig => {
  return {
    /* ICAv2 Pipeline analysis essentials */
    icav2TokenSecretId: icav2AccessTokenSecretName[stage], // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
    pipelineIdSsmPath: wgtsQcIcav2PipelineIdSSMParameterPath, // List of parameters the workflow session state machine will need access to
    /* Table to store analyis metadata */
    dynamodbTableName: wgtsQcIcav2PipelineManagerDynamodbTableName,
    /* Internal and external buses */
    eventBusName: eventBusName,
    icaEventPipeName: `${icaEventPipeStackName}Pipe`,
    /* Event handling */
    workflowType: wgtsQcIcav2PipelineWorkflowType,
    workflowVersion: wgtsQcIcav2PipelineWorkflowTypeVersion,
    serviceVersion: wgtsQcIcav2ServiceVersion,
    triggerLaunchSource: wgtsQcIcav2ReadyEventSource,
    internalEventSource: wgtsQcIcav2EventSource,
    detailType: wgtsQcIcav2EventDetailType,
    /* Names for statemachines */
    stateMachinePrefix: wgtsQcStateMachinePrefix,
    /* SSM Workflow Parameters */
    annotationUriSsmPath: wgtsQcIcav2AnnotationUriMappingSSMParameterPath,
    defaultReferenceVersion: wgtsQcDefaultReferenceVersion,
    referenceUriSsmPath: wgtsQcIcav2ReferenceUriMappingSSMParameterPath,
    defaultAnnotationVersion: wgtsQcDefaultAnnotationVersion,
  };
};
