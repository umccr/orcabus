import {
  AppStage,
  eventBusName,
  icav2AccessTokenSecretName,
  pieriandxAuthTokeSsmParameterPath,
  pieriandxBaseUrlSsmParameterPath,
  pieriandxDagSsmParameterPath,
  pieriandxDefaultDagName,
  pieriandxDefaultPanelName,
  pieriandxDetailType,
  pieriandxDynamodbTable,
  pieriandxEventSource,
  pieriandxInstitutionSsmParameterPath,
  pieriandxPanelMapSsmParameterPath,
  pieriandxPayloadVersion,
  pieriandxPrefix,
  pieriandxS3CredentialsSecretsManagerId,
  pieriandxS3SequencerRunRootSsmParameterPath,
  pieriandxTriggerLaunchSource,
  pieriandxUserEmailSsmParameterPath,
  pieriandxWorkflowName,
  pieriandxWorkflowVersion,
} from '../constants';
import { PierianDxPipelineTableConfig } from '../../lib/workload/stateful/stacks/pieriandx-pipeline-dynamo-db/deploy';
import { PierianDxPipelineManagerConfig } from '../../lib/workload/stateless/stacks/pieriandx-pipeline-manager/deploy';

// Stateful
export const getPierianDxPipelineTableStackProps = (): PierianDxPipelineTableConfig => {
  return {
    dynamodbTableName: pieriandxDynamodbTable,
  };
};

// Stateless
export const getPierianDxPipelineManagerStackProps = (
  stage: AppStage
): PierianDxPipelineManagerConfig => {
  return {
    /* DynamoDB Table */
    dynamodbTableName: pieriandxDynamodbTable,
    /* Workflow knowledge */
    workflowName: pieriandxWorkflowName,
    workflowVersion: pieriandxWorkflowVersion,
    /* Default values */
    defaultDagVersion: pieriandxDefaultDagName,
    defaultPanelName: pieriandxDefaultPanelName,
    /* Secrets */
    /* ICAv2 Pipeline analysis essentials */
    icav2AccessTokenSecretId: icav2AccessTokenSecretName[stage], // "/icav2/umccr-prod/service-production-jwt-token-secret-arn"
    pieriandxS3AccessTokenSecretId: pieriandxS3CredentialsSecretsManagerId, // "/pieriandx/s3AccessCredentials"
    /* SSM Parameters */
    dagSsmParameterPath: pieriandxDagSsmParameterPath,
    panelNameSsmParameterPath: pieriandxPanelMapSsmParameterPath,
    s3SequencerRunRootSsmParameterPath: pieriandxS3SequencerRunRootSsmParameterPath,
    /*
        Pieriandx specific parameters
        */
    pieriandxUserEmailSsmParameterPath: pieriandxUserEmailSsmParameterPath,
    pieriandxInstitutionSsmParameterPath: pieriandxInstitutionSsmParameterPath,
    pieriandxBaseUrlSsmParameterPath: pieriandxBaseUrlSsmParameterPath,
    pieriandxAuthTokenCollectionLambdaFunctionName: pieriandxAuthTokeSsmParameterPath,
    /* Event info */
    eventDetailType: pieriandxDetailType,
    eventBusName: eventBusName,
    eventSource: pieriandxEventSource,
    payloadVersion: pieriandxPayloadVersion,
    triggerLaunchSource: pieriandxTriggerLaunchSource,
    /* Custom */
    prefix: pieriandxPrefix,
  };
};
