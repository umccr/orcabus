import {
  AppStage,
  eventBusName,
  icaEventPipeStackName,
  icav2AccessTokenSecretName,
  umccriseIcav2PipelineIdSSMParameterPath,
  umccriseIcav2PipelineManagerDynamodbTableName,
  umccriseIcav2PipelineWorkflowType,
  umccriseIcav2PipelineWorkflowTypeVersion,
  umccriseIcav2ServiceVersion,
  umccriseIcav2ReadyEventSource,
  umccriseIcav2EventSource,
  umccriseIcav2EventDetailType,
  umccriseStateMachinePrefix,
  umccriseDefaultGenomeVersion,
  umccriseDynamoDbTableSSMArn,
  umccriseDynamoDbTableSSMName,
  icav2UmccriseGenomesReferenceUriMappingSSMParameterPath,
} from '../constants';
import { UmccriseIcav2PipelineManagerConfig } from '../../lib/workload/stateless/stacks/umccrise-pipeline-manager/deploy';
import { UmccriseIcav2PipelineTableConfig } from '../../lib/workload/stateful/stacks/umccrise-pipeline-dynamo-db/deploy/stack';

// Stateful
export const getUmccriseIcav2PipelineTableStackProps = (): UmccriseIcav2PipelineTableConfig => {
  return {
    umccriseIcav2DynamodbTableArnSsmParameterPath: umccriseDynamoDbTableSSMArn,
    umccriseIcav2DynamodbTableNameSsmParameterPath: umccriseDynamoDbTableSSMName,
    dynamodbTableName: umccriseIcav2PipelineManagerDynamodbTableName,
  };
};

// Stateless
export const getUmccriseIcav2PipelineManagerStackProps = (
  stage: AppStage
): UmccriseIcav2PipelineManagerConfig => {
  return {
    /* ICAv2 Pipeline analysis essentials */
    icav2TokenSecretId: icav2AccessTokenSecretName[stage], // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
    pipelineIdSsmPath: umccriseIcav2PipelineIdSSMParameterPath, // List of parameters the workflow session state machine will need access to
    /* Table to store analyis metadata */
    dynamodbTableName: umccriseIcav2PipelineManagerDynamodbTableName,
    /* Internal and external buses */
    eventBusName: eventBusName,
    icaEventPipeName: `${icaEventPipeStackName}Pipe`,
    /* Event handling */
    workflowType: umccriseIcav2PipelineWorkflowType,
    workflowVersion: umccriseIcav2PipelineWorkflowTypeVersion,
    serviceVersion: umccriseIcav2ServiceVersion,
    triggerLaunchSource: umccriseIcav2ReadyEventSource,
    internalEventSource: umccriseIcav2EventSource,
    detailType: umccriseIcav2EventDetailType,
    /* Names for statemachines */
    stateMachinePrefix: umccriseStateMachinePrefix,
    /* SSM Workflow Parameters */
    defaultReferenceVersion: umccriseDefaultGenomeVersion,
    referenceUriSsmPath: icav2UmccriseGenomesReferenceUriMappingSSMParameterPath,
  };
};
