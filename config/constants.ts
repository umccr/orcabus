import { VpcLookupOptions } from 'aws-cdk-lib/aws-ec2';

export type AccountName = 'beta' | 'gamma' | 'prod';

export const region = 'ap-southeast-2';

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

export const devBucket = 'umccr-temp-dev';
export const stgBucket = 'umccr-temp-stg';
export const prodBucket = 'org.umccr.data.oncoanalyser';

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
export const regName = 'OrcaBusSchemaRegistry';
export const eventBusName = 'OrcaBusMain';
export const eventSourceQueueName = 'orcabus-event-source-queue';

/**
 * Configuration for resources created in TokenServiceStack
 */

export const serviceUserSecretName = 'orcabus/token-service-user'; // pragma: allowlist secret
export const jwtSecretName = 'orcabus/token-service-jwt'; // pragma: allowlist secret

// const statelessConfig = {
//   multiSchemaConstructProps: {
//     registryName: regName,
//     schemas: [
//       {
//         schemaName: 'BclConvertWorkflowRequest',
//         schemaDescription: 'Request event for BclConvertWorkflow',
//         schemaType: 'OpenApi3',
//         schemaLocation: __dirname + '/event_schemas/BclConvertWorkflowRequest.json',
//       },
//       {
//         schemaName: 'DragenWgsQcWorkflowRequest',
//         schemaDescription: 'Request event for DragenWgsQcWorkflowRequest',
//         schemaType: 'OpenApi3',
//         schemaLocation: __dirname + '/event_schemas/DragenWgsQcWorkflowRequest.json',
//       },
//     ],
//   },
//   eventBusName: eventBusName,
//   computeSecurityGroupName: computeSecurityGroupName,
//   rdsMasterSecretName: rdsMasterSecretName,
// };
