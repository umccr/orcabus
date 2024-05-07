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
export const schemaRegistryName = 'orcabus.events';
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

/*
ICAv2 Resources - required by various stacks
 */
export const icav2AccessTokenSecretName: Record<AppStage, string> = {
  [AppStage.BETA]: 'ICAv2JWTKey-umccr-prod-service-trial', // pragma: allowlist secret
  [AppStage.GAMMA]: 'ICAv2JWTKey-umccr-prod-service-staging', // pragma: allowlist secret
  [AppStage.PROD]: 'ICAv2JWTKey-umccr-prod-service-prod', // pragma: allowlist secret
};

/*
Resources generated by the ICAv2 Copy Batch utility stack
 */
export const icav2CopyBatchSSMRoot = '/orcabus/icav2_copy_batch_utility';
export const icav2CopyBatchSSMBatchArn = path.join(icav2CopyBatchSSMRoot, 'batch_sfn_arn');
export const icav2CopyBatchSSMBatchName = path.join(icav2CopyBatchSSMRoot, 'batch_sfn_name');
export const icav2CopyBatchSSMSingleArn = path.join(icav2CopyBatchSSMRoot, 'single_sfn_arn');
export const icav2CopyBatchSSMSingleName = path.join(icav2CopyBatchSSMRoot, 'single_sfn_name');
export const icav2CopyBatchUtilityName = 'icav2_copy_batch_utility_sfn';
export const icav2CopySingleUtilityName = 'icav2_copy_single_utility_sfn';

/*
Resources generated by the BSSH Fastq Copy Manager
 */

export const bsshFastqCopyManagerSSMRoot = '/orcabus/bssh_icav2_fastq_copy_manager';
export const bsshFastqCopyManagerSSMName = path.join(
  bsshFastqCopyManagerSSMRoot,
  'state_machine_name'
);
export const bsshFastqCopyManagerSSMArn = path.join(
  bsshFastqCopyManagerSSMRoot,
  'state_machine_arn'
);
export const bsshFastqCopyManagerSfnName = 'bssh_fastq_copy_manager_sfn';

/*
External resources required by the ctTSO v2 Stack
*/
export const cttsov2Icav2PipelineIdSSMParameterPath =
  '/icav2/umccr-prod/tso500_ctdna_2.1_pipeline_id';

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

// Stateless
export const cttsov2Icav2PipelineSfnSSMName = path.join(
  cttsov2Icav2PipelineManagerSSMRoot,
  'state_machine_name'
);
export const cttsov2Icav2PipelineSfnSSMArn = path.join(
  cttsov2Icav2PipelineManagerSSMRoot,
  'state_machine_arn'
);

export const cttsov2Icav2PipelineWorkflowType = 'cttsov2';
export const cttsov2Icav2PipelineWorkflowTypeVersion = '2.1.1';
export const cttsov2Icav2ServiceVersion = '2024.05.07';
