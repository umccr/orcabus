import { VpcLookupOptions } from 'aws-cdk-lib/aws-ec2';
import path from 'path';

export enum AppStage {
  BETA = 'beta',
  GAMMA = 'gamma',
  PROD = 'prod',
}

export const region = 'ap-southeast-2';

/**
 * accountIdAlias: mapping from AccountName to AWS Account ID.
 */
export const accountIdAlias: Record<AppStage, string> = {
  [AppStage.BETA]: '843407916570', // umccr_development
  [AppStage.GAMMA]: '455634345446', // umccr_staging
  [AppStage.PROD]: '472057503814', // umccr_production
};

// external ICA constants
export const icaAwsAccountNumber = '079623148045';

// Name of the Ica Event Pipe stack
export const icaEventPipeStackName = 'IcaEventPipeStack';

// upstream infra: vpc
const vpcName = 'main-vpc';
const vpcStackName = 'networking';
export const vpcProps: VpcLookupOptions = {
  vpcName: vpcName,
  tags: {
    Stack: vpcStackName,
  },
};

// upstream infra: cognito
export const cognitoUserPoolIdParameterName = '/data_portal/client/cog_user_pool_id';
export const cognitoPortalAppClientIdParameterName =
  '/data_portal/client/data2/cog_app_client_id_stage';
export const cognitoStatusPageAppClientIdParameterName =
  '/data_portal/status_page/cog_app_client_id_stage';
export const cognitoApiGatewayProps = {
  cognitoUserPoolIdParameterName: cognitoUserPoolIdParameterName,
  cognitoPortalAppClientIdParameterName: cognitoPortalAppClientIdParameterName,
  cognitoStatusPageAppClientIdParameterName: cognitoStatusPageAppClientIdParameterName,
};

export const oncoanalyserBucket: Record<AppStage, string> = {
  [AppStage.BETA]: 'umccr-temp-dev',
  [AppStage.GAMMA]: 'umccr-temp-stg',
  [AppStage.PROD]: 'org.umccr.data.oncoanalyser',
};

export const icav2PipelineCacheBucket: Record<AppStage, string> = {
  [AppStage.BETA]: 'pipeline-dev-cache-503977275616-ap-southeast-2',
  [AppStage.GAMMA]: 'pipeline-stg-cache-503977275616-ap-southeast-2',
  [AppStage.PROD]: 'pipeline-prod-cache-503977275616-ap-southeast-2',
};

export const gdsBsRunsUploadLogPath: Record<AppStage, string> = {
  [AppStage.BETA]: 'gds://development/primary_data/temp/bs_runs_upload_tes/',
  [AppStage.GAMMA]: 'gds://staging/primary_data/temp/bs_runs_upload_tes/',
  [AppStage.PROD]: 'gds://production/primary_data/temp/bs_runs_upload_tes/',
};

/**
 * Validate the secret name so that it doesn't end with 6 characters and a hyphen.
 *
 */
export const validateSecretName = (secretName: string) => {
  // Note, this should not end with a hyphen and 6 characters, otherwise secrets manager won't be
  // able to find the secret using a partial ARN.
  if (/-(.){6}$/.test(secretName)) {
    throw new Error('the secret name should not end with a hyphen and 6 characters');
  }
};

/**
 * Configuration for resources created in SharedStack
 */
// Db Construct
export const computeSecurityGroupName = 'OrcaBusSharedComputeSecurityGroup';
export const dbClusterIdentifier = 'orcabus-db';
export const dbClusterResourceIdParameterName = '/orcabus/db-cluster-resource-id';
export const dbClusterEndpointHostParameterName = '/orcabus/db-cluster-endpoint-host';
export const databasePort = 5432;

export const rdsMasterSecretName = 'orcabus/master-rds'; // pragma: allowlist secret
validateSecretName(rdsMasterSecretName);

// Other constants that exist in the SharedStack
export const eventSchemaRegistryName = 'orcabus.events';
export const dataSchemaRegistryName = 'orcabus.data';
export const eventBusName = 'OrcaBusMain';
export const eventSourceQueueName = 'orcabus-event-source-queue';

/**
 * Configuration for resources created in TokenServiceStack
 */

export const serviceUserSecretName = 'orcabus/token-service-user'; // pragma: allowlist secret
export const jwtSecretName = 'orcabus/token-service-jwt'; // pragma: allowlist secret
export const icaAccessTokenSecretName = 'IcaSecretsPortal'; // pragma: allowlist secret

/*
Resources required for BaseSpace TES stack
 */

export const basespaceAccessTokenSecretName = '/manual/BaseSpaceAccessTokenSecret'; // pragma: allowlist secret
export const ssCheckApiDomainSsmParameterName = '/sscheck/lambda-api-domain';

/*
ICAv2 Resources - required by various stacks
 */
export const icav2AccessTokenSecretName: Record<AppStage, string> = {
  [AppStage.BETA]: 'ICAv2JWTKey-umccr-prod-service-dev', // pragma: allowlist secret
  [AppStage.GAMMA]: 'ICAv2JWTKey-umccr-prod-service-staging', // pragma: allowlist secret
  [AppStage.PROD]: 'ICAv2JWTKey-umccr-prod-service-prod', // pragma: allowlist secret
};

/*
Resources generated by the BSSH Fastq Copy Manager
*/

export const bsshFastqCopyManagerWorkflowName = 'bsshFastqCopy';
export const bsshFastqCopyManagerWorkflowTypeVersion = '1.0.0';
export const bsshFastqCopyManagerServiceVersion = '2024.05.15';

export const bsshFastqCopyManagerReadyEventSource = 'orcabus.workflowmanager';
export const bsshFastqCopyManagerEventSource = 'orcabus.bsshfastqcopymanager';
export const bsshFastqCopyManagerEventDetailType = 'WorkflowRunStateChange';

/*
Resources generated by the BCLConvert InterOp QC pipeline
*/

export const bclConvertInteropQcSSMRoot = '/orcabus/bclconvert_interop_qc';

export const bclconvertInteropQcIcav2PipelineManagerDynamodbTableName =
  'bclconvertInteropQcICAv2AnalysesDynamoDBTable';

// Stateful
export const bclconvertInteropQcDynamoDbTableSSMName = path.join(
  bclConvertInteropQcSSMRoot,
  'dynamodb_table_name'
);
export const bclconvertInteropQcDynamoDbTableSSMArn = path.join(
  bclConvertInteropQcSSMRoot,
  'dynamodb_table_arn'
);

// Stateless

export const bclconvertInteropQcIcav2PipelineWorkflowName = 'bclconvert_interop_qc';
export const bclconvertInteropQcIcav2PipelineWorkflowTypeVersion = '1.3.1--1.21';
export const bclconvertInteropQcIcav2ServiceVersion = '2024.05.07';

export const bclconvertInteropQcIcav2ReadyEventSource = 'orcabus.workflowmanager';
export const bclconvertInteropQcIcav2EventSource = 'orcabus.bclconvertinteropqc';
export const bclconvertInteropQcIcav2EventDetailType = 'WorkflowRunStateChange';
export const bclconvertInteropQcStateMachinePrefix = 'bclconvertInteropQcSfn';

/*
Resources used by the bclConvert InteropQc Pipeline
*/
export const bclconvertInteropQcIcav2PipelineIdSSMParameterPath =
  '/icav2/umccr-prod/bclconvert_interop_qc_pipeline_id';

/*
External resources required by the ctTSO v2 Stack
*/
export const cttsov2Icav2PipelineIdSSMParameterPath =
  '/icav2/umccr-prod/tso500_ctdna_2.5_pipeline_id';

/*
Resources generated by the ctTSO v2 Stack
*/
export const cttsov2Icav2PipelineManagerSSMRoot = '/orcabus/ctTSOv2';

// Stateful
export const cttsov2Icav2PipelineManagerDynamodbTableName = 'ctTSOv2ICAv2AnalysesDynamoDBTable';
export const cttsov2DynamoDbTableSSMName = path.join(
  cttsov2Icav2PipelineManagerSSMRoot,
  'dynamodb_table_name'
);
export const cttsov2DynamoDbTableSSMArn = path.join(
  cttsov2Icav2PipelineManagerSSMRoot,
  'dynamodb_table_arn'
);

// Event Handling

export const cttsov2Icav2PipelineWorkflowType = 'cttsov2';
export const cttsov2Icav2PipelineWorkflowTypeVersion = '2.5.0';
export const cttsov2Icav2ServiceVersion = '2024.05.07';

export const cttsov2Icav2ReadyEventSource = 'orcabus.workflowmanager';
export const cttsov2Icav2EventSource = 'orcabus.cttsov2';
export const cttsov2Icav2EventDetailType = 'WorkflowRunStateChange';
export const cttsov2StateMachinePrefix = 'cttsov2Sfn';

// Mock Stack
export const mockEventBusName = eventBusName;
export const mockInstrumentRunTableName = 'stacky-instrument-run-table';
export const mockInputMakerTableName = 'stacky-input-maker-table';
export const mockWorkflowManagerTableName = 'stacky-workflow-manager-table';
export const mockIcav2ProjectIdSsmParameterName = '/orcabus/stacky/icav2_project_id_and_name_json';
export const mockPrimaryOutputUriSsmParameterName = '/orcabus/stacky/primary_output_uri'; // icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/primary_data/__instrument_run_id__/__portal_run_id__/
export const mockAnalysisOutputUriSsmParameterName = '/orcabus/stacky/analysis_output_uri'; // icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/analysis_data/__workflow_name__/__workflow_version__/__portal_run_id__/
export const mockAnalysisLogsUriSsmParameterName = '/orcabus/stacky/analysis_logs_uri'; // icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/analysis_logs/__workflow_name__/__workflow_version__/__portal_run_id__/

export const mockAnalysisCacheUriSsmParameterName = '/orcabus/stacky/analysis_cache_uri'; // icav2://7595e8f2-32d3-4c76-a324-c6a85dae87b5/analysis_cache/__workflow_name__/__workflow_version__/__portal_run_id__/
