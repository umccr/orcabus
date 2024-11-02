import {
  AppStage,
  eventBusName,
  icaEventPipeStackName,
  icav2AccessTokenSecretName,
  oraCompressionIcav2PipelineIdSSMParameterPath,
  oraCompressionIcav2PipelineManagerDynamodbTableName,
  oraCompressionIcav2PipelineWorkflowType,
  oraCompressionIcav2PipelineWorkflowTypeVersion,
  oraCompressionIcav2ServiceVersion,
  oraCompressionIcav2ReadyEventSource,
  oraCompressionIcav2EventSource,
  oraCompressionIcav2EventDetailType,
  oraCompressionDynamoDbTableSSMArn,
  oraCompressionDynamoDbTableSSMName,
  oraCompressionDefaultReferenceUriSSmParameterPath,
  oraCompressionStateMachinePrefix,
} from '../constants';
import { OraCompressionIcav2PipelineTableConfig } from '../../lib/workload/stateful/stacks/ora-decompression-dynamodb/deploy/stack';
import { OraCompressionIcav2PipelineManagerConfig } from '../../lib/workload/stateless/stacks/ora-compression-manager/deploy';

// Stateful
export const getOraCompressionIcav2PipelineTableStackProps =
  (): OraCompressionIcav2PipelineTableConfig => {
    return {
      oraDecompressionIcav2DynamodbTableArnSsmParameterPath: oraCompressionDynamoDbTableSSMArn,
      oraDecompressionIcav2DynamodbTableNameSsmParameterPath: oraCompressionDynamoDbTableSSMName,
      dynamodbTableName: oraCompressionIcav2PipelineManagerDynamodbTableName,
    };
  };

// Stateless
export const getOraCompressionIcav2PipelineManagerStackProps = (
  stage: AppStage
): OraCompressionIcav2PipelineManagerConfig => {
  return {
    /* ICAv2 Pipeline analysis essentials */
    icav2TokenSecretId: icav2AccessTokenSecretName[stage], // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
    /* Table to store analyis metadata */
    dynamodbTableName: oraCompressionIcav2PipelineManagerDynamodbTableName,
    /* Internal and external buses */
    eventBusName: eventBusName,
    icaEventPipeName: `${icaEventPipeStackName}Pipe`,
    /* Event handling */
    workflowName: oraCompressionIcav2PipelineWorkflowType,
    workflowVersion: oraCompressionIcav2PipelineWorkflowTypeVersion,
    serviceVersion: oraCompressionIcav2ServiceVersion,
    triggerLaunchSource: oraCompressionIcav2ReadyEventSource,
    internalEventSource: oraCompressionIcav2EventSource,
    detailType: oraCompressionIcav2EventDetailType,
    /* Names for statemachines */
    stateMachinePrefix: oraCompressionStateMachinePrefix,
    /* SSM Workflow Parameters */
    referenceUriSsmPath: oraCompressionDefaultReferenceUriSSmParameterPath,
    pipelineIdSsmPath: oraCompressionIcav2PipelineIdSSMParameterPath, // List of parameters the workflow session state machine will need access to
  };
};
