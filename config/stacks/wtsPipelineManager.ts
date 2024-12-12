import {
  AppStage,
  eventBusName,
  icaEventPipeStackName,
  icav2AccessTokenSecretName,
  dragenIcav2ReferenceUriMappingSSMParameterPath,
  wtsIcav2PipelineIdSSMParameterPath,
  wtsIcav2PipelineManagerDynamodbTableName,
  wtsIcav2PipelineWorkflowType,
  wtsIcav2PipelineWorkflowTypeVersion,
  wtsIcav2ServiceVersion,
  wtsIcav2ReadyEventSource,
  wtsIcav2EventSource,
  wtsIcav2EventDetailType,
  wtsStateMachinePrefix,
  wtsDynamoDbTableSSMArn,
  wtsDynamoDbTableSSMName,
  icav2ArribaUriMappingSSMParameterPath,
  wtsDefaultDragenReferenceVersion,
  wtsDefaultFastaReferenceVersion,
  wtsDefaultQcReferenceSamplesVersion,
  wtsDefaultArribaVersion,
  wtsDefaultGencodeAnnotationVersion,
  icav2FastaReferenceUriMappingSSMParameterPath,
  icav2GencodeAnnotationUriMappingSSMParameterPath,
  icav2WtsQcReferenceSamplesUriMappingSSMParameterPath,
  dragenIcav2OraReferenceUriSSMParameterPath,
} from '../constants';
import { WtsIcav2PipelineManagerConfig } from '../../lib/workload/stateless/stacks/transcriptome-pipeline-manager/deploy';
import { WtsIcav2PipelineTableConfig } from '../../lib/workload/stateful/stacks/wts-dynamo-db/deploy/stack';

// Stateful
export const getWtsIcav2PipelineTableStackProps = (): WtsIcav2PipelineTableConfig => {
  return {
    wtsIcav2DynamodbTableArnSsmParameterPath: wtsDynamoDbTableSSMArn,
    wtsIcav2DynamodbTableNameSsmParameterPath: wtsDynamoDbTableSSMName,
    dynamodbTableName: wtsIcav2PipelineManagerDynamodbTableName,
  };
};

// Stateless
export const getWtsIcav2PipelineManagerStackProps = (
  stage: AppStage
): WtsIcav2PipelineManagerConfig => {
  return {
    /* ICAv2 Pipeline analysis essentials */
    icav2TokenSecretId: icav2AccessTokenSecretName[stage], // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
    pipelineIdSsmPath: wtsIcav2PipelineIdSSMParameterPath, // List of parameters the workflow session state machine will need access to
    /* Table to store analyis metadata */
    dynamodbTableName: wtsIcav2PipelineManagerDynamodbTableName,
    /* Internal and external buses */
    eventBusName: eventBusName,
    icaEventPipeName: `${icaEventPipeStackName}Pipe`,
    /* Event handling */
    workflowType: wtsIcav2PipelineWorkflowType,
    workflowVersion: wtsIcav2PipelineWorkflowTypeVersion,
    serviceVersion: wtsIcav2ServiceVersion,
    triggerLaunchSource: wtsIcav2ReadyEventSource,
    internalEventSource: wtsIcav2EventSource,
    detailType: wtsIcav2EventDetailType,
    /* Names for statemachines */
    stateMachinePrefix: wtsStateMachinePrefix,
    /* SSM Parameters */
    arribaUriSsmPath: icav2ArribaUriMappingSSMParameterPath,
    dragenReferenceUriSsmPath: dragenIcav2ReferenceUriMappingSSMParameterPath,
    fastaReferenceUriSsmPath: icav2FastaReferenceUriMappingSSMParameterPath,
    gencodeAnnotationUriSsmPath: icav2GencodeAnnotationUriMappingSSMParameterPath,
    wtsQcReferenceSamplesSsmPath: icav2WtsQcReferenceSamplesUriMappingSSMParameterPath,
    oraReferenceUriSsmPath: dragenIcav2OraReferenceUriSSMParameterPath,
    /* Default Versions */
    defaultArribaVersion: wtsDefaultArribaVersion,
    defaultDragenReferenceVersion: wtsDefaultDragenReferenceVersion,
    defaultFastaReferenceVersion: wtsDefaultFastaReferenceVersion,
    defaultGencodeAnnotationVersion: wtsDefaultGencodeAnnotationVersion,
    defaultQcReferenceSamplesVersion: wtsDefaultQcReferenceSamplesVersion,
  };
};
