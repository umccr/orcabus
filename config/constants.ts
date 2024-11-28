import { RemovalPolicy } from 'aws-cdk-lib';
import { VpcLookupOptions } from 'aws-cdk-lib/aws-ec2';
import { RetentionDays } from 'aws-cdk-lib/aws-logs';
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

/**
 * The SSM Parameter Name for HTTP Lambda Authorizer ARN defined in authorization stack manager
 */
export const authStackHttpLambdaAuthorizerParameterName =
  '/orcabus/authorization-stack/http-lambda-authorization-arn';

// upstream infra: cognito
export const cognitoPortalAppClientIdParameterName =
  '/data_portal/client/data2/cog_app_client_id_stage';
export const cognitoUserPoolIdParameterName = '/data_portal/client/cog_user_pool_id';
export const logsApiGatewayConfig = {
  [AppStage.BETA]: {
    retention: RetentionDays.TWO_WEEKS,
    removalPolicy: RemovalPolicy.DESTROY,
  },
  [AppStage.GAMMA]: {
    retention: RetentionDays.TWO_WEEKS,
    removalPolicy: RemovalPolicy.DESTROY,
  },
  [AppStage.PROD]: {
    retention: RetentionDays.TWO_YEARS,
    removalPolicy: RemovalPolicy.RETAIN,
  },
};
export const corsAllowOrigins = {
  [AppStage.BETA]: ['https://orcaui.dev.umccr.org'],
  [AppStage.GAMMA]: ['https://orcaui.stg.umccr.org'],
  [AppStage.PROD]: ['https://orcaui.prod.umccr.org', 'https://orcaui.umccr.org'],
};
export const cognitoApiGatewayConfig = {
  region,
  cognitoUserPoolIdParameterName,
  cognitoClientIdParameterNameArray: [
    cognitoPortalAppClientIdParameterName, // portal - TokenServiceStack
    '/orcaui/cog_app_client_id_stage', // orcaui - https://github.com/umccr/orca-ui
  ],
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

// The archive bucket. Noting that this is only present for prod data.
export const icav2ArchiveAnalysisBucket: Record<AppStage.PROD, string> = {
  [AppStage.PROD]: 'archive-prod-analysis-503977275616-ap-southeast-2',
};

// The fastq bucket. Noting that this is only present for prod data.
export const icav2ArchiveFastqBucket: Record<AppStage.PROD, string> = {
  [AppStage.PROD]: 'archive-prod-fastq-503977275616-ap-southeast-2',
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

// DLQs for stateless stack functions
export const eventDlqNameFMAnnotator = 'orcabus-event-dlq-fmannotator';

/**
 * Configuration for resources created in TokenServiceStack
 */

export const serviceUserSecretName = 'orcabus/token-service-user'; // pragma: allowlist secret
export const jwtSecretName = 'orcabus/token-service-jwt'; // pragma: allowlist secret
export const icaAccessTokenSecretName = 'IcaSecretsPortal'; // pragma: allowlist secret

export const fileManagerIngestRoleName = 'orcabus-file-manager-ingest-role';

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
  [AppStage.PROD]: 'ICAv2JWTKey-umccr-prod-service-production', // pragma: allowlist secret
};

/*
Resources generated by the BSSH Fastq Copy Manager
*/

export const bsshFastqCopyManagerWorkflowName = 'bsshFastqCopy';
export const bsshFastqCopyManagerWorkflowTypeVersion = '1.0.0';
export const bsshFastqCopyManagerServiceVersion = '2024.07.01';

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
export const bclconvertInteropQcIcav2PipelineWorkflowName = 'bclconvert-interop-qc';
export const bclconvertInteropQcIcav2PipelineWorkflowTypeVersion = '1.3.1--1.21';
export const bclconvertInteropQcIcav2ServiceVersion = '2024.07.01';

export const bclconvertInteropQcIcav2ReadyEventSource = 'orcabus.workflowmanager';
export const bclconvertInteropQcIcav2EventSource = 'orcabus.bclconvertinteropqc';
export const bclconvertInteropQcIcav2EventDetailType = 'WorkflowRunStateChange';
export const bclconvertInteropQcStateMachinePrefix = 'bclconvertInteropQcSfn';

/*
Resources used by the bclConvert InteropQc Pipeline
*/

// Release can be found here: https://github.com/umccr/cwl-ica/releases/tag/bclconvert-interop-qc%2F1.3.1--1.21__20241119001529
// Pipeline ID is: a147ad9f-af8f-409d-95b7-49018782ab4d
export const bclconvertInteropQcIcav2PipelineIdSSMParameterPath =
  '/icav2/umccr-prod/bclconvert_interop_qc_pipeline_id';

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
export const cttsov2Icav2PipelineWorkflowTypeVersion = '2.6.0';
export const cttsov2Icav2ServiceVersion = '2024.07.01';

export const cttsov2Icav2ReadyEventSource = 'orcabus.workflowmanager';
export const cttsov2Icav2EventSource = 'orcabus.cttsov2';
export const cttsov2Icav2EventDetailType = 'WorkflowRunStateChange';
export const cttsov2StateMachinePrefix = 'cttsov2Sfn';

/*
External resources required by the ctTSO v2 Stack
*/

// Deployed under dev/stg/prod
export const cttsov2Icav2PipelineIdSSMParameterPath =
  '/icav2/umccr-prod/tso500_ctdna_2.6_pipeline_id';

/*
Resources generated by the WGTS QC Stateful Stack
*/
export const wgtsQcIcav2PipelineManagerSSMRoot = '/orcabus/wgtsQc';

// Stateful
export const wgtsQcIcav2PipelineManagerDynamodbTableName = 'wgtsQcICAv2AnalysesDynamoDBTable';
export const wgtsQcDynamoDbTableSSMName = path.join(
  wgtsQcIcav2PipelineManagerSSMRoot,
  'dynamodb_table_name'
);
export const wgtsQcDynamoDbTableSSMArn = path.join(
  wgtsQcIcav2PipelineManagerSSMRoot,
  'dynamodb_table_arn'
);

/*
External resources required by all dragen stacks on ICAv2
*/

// Deployed under dev/stg/prod
// '
//   [
//     {
//       "name": "v9-r3",
//       "uri": "icav2://reference-data/dragen-hash-tables/v9-r3/hg38-alt_masked-cnv-hla-rna/hg38-alt_masked.cnv.hla.rna-9-r3.0-1.tar.gz"
//     }
//   ]
// '
export const dragenIcav2ReferenceUriMappingSSMParameterPath =
  '/icav2/umccr-prod/dragen_reference_mapping';

// Deployed under dev/stg/prod
// '
//   [
//     {
//       "name": "v39",
//       "uri": "icav2://reference-data/gencode/hg38/v39/gencode.v39.annotation.gtf"
//     }
//   ]
// '
export const icav2GencodeAnnotationUriMappingSSMParameterPath =
  '/icav2/umccr-prod/wts_qc_annotation_mapping';

// Deployed under dev/stg/prod
// '
//   [
//     {
//       "name": "hg38",
//       "uri": "icav2://reference-data/genomes/hg38/hg38.fa"
//     }
//   ]
// '
export const icav2FastaReferenceUriMappingSSMParameterPath =
  '/icav2/umccr-prod/fasta_reference_mapping'; //

/*
External resources required by the wgtsqc Stack
*/

// Deployed under dev/stg/prod
export const wgtsQcIcav2PipelineIdSSMParameterPath = '/icav2/umccr-prod/wgts_qc_4.2.4_pipeline_id'; // 03689516-b7f8-4dca-bba9-8405b85fae45

export const wgtsQcIcav2PipelineWorkflowType = 'wgts-qc';
export const wgtsQcIcav2PipelineWorkflowTypeVersion = '4.2.4';
export const wgtsQcIcav2ServiceVersion = '2024.07.01';

export const wgtsQcIcav2ReadyEventSource = 'orcabus.workflowmanager';
export const wgtsQcIcav2EventSource = 'orcabus.wgtsqc';
export const wgtsQcIcav2EventDetailType = 'WorkflowRunStateChange';
export const wgtsQcStateMachinePrefix = 'wgtsQcSfn';

export const wgtsQcDefaultReferenceVersion = 'v9-r3';
export const wgtsQcDefaultAnnotationVersion = 'v39';

// Tumor Normal pipeline

/*
Resources generated by the Tn Stateful Stack
*/
export const tnIcav2PipelineManagerSSMRoot = '/orcabus/tumor_normal';

// Stateful
export const tnIcav2PipelineManagerDynamodbTableName = 'tnICAv2AnalysesDynamoDBTable';
export const tnDynamoDbTableSSMName = path.join(
  tnIcav2PipelineManagerSSMRoot,
  'dynamodb_table_name'
);
export const tnDynamoDbTableSSMArn = path.join(tnIcav2PipelineManagerSSMRoot, 'dynamodb_table_arn');

/*
TN Stateless stack
*/

// Deployed under dev/stg/prod
export const tnIcav2PipelineIdSSMParameterPath = '/icav2/umccr-prod/tumor_normal_4.2.4_pipeline_id'; // 6ce2b636-ba2f-4004-8065-f3557f286c98
export const tnIcav2PipelineWorkflowType = 'tumor-normal';
export const tnIcav2PipelineWorkflowTypeVersion = '4.2.4';
export const tnIcav2ServiceVersion = '2024.07.01';
export const tnIcav2ReadyEventSource = 'orcabus.workflowmanager';
export const tnIcav2EventSource = 'orcabus.tumornormal';
export const tnIcav2EventDetailType = 'WorkflowRunStateChange';
export const tnStateMachinePrefix = 'tnSfn';
export const tnDefaultReferenceVersion = 'v9-r3';

// WTS pipeline

/*
Resources required by the WTS Stateful Stack
*/

// Deployed under dev/stg/prod
// '[
//     {
//         "name": "2.4.0",
//         "blacklist_uri": "icav2://reference-data/arriba/2-4-0/blacklist_hg38_GRCh38_v2.4.0.tsv.gz",
//         "cytobands_uri": "icav2://reference-data/arriba/2-4-0/cytobands_hg38_GRCh38_v2.4.0.tsv",
//         "protein_domains_uri": "icav2://reference-data/arriba/2-4-0/protein_domains_hg38_GRCh38_v2.4.0.gff3"
//     }
//  ]'
export const icav2ArribaUriMappingSSMParameterPath = '/icav2/umccr-prod/arriba_mapping';

// Deployed under dev/stg/prod
// '[
//    {
//        "name": "2023-07-21--4.2.4",
//        "qc_reference_samples_json":  [
//          "icav2://reference-data/dragen-wts-multiqc/2023-07-21--4-2-4/SBJ01563/",
//          "icav2://reference-data/dragen-wts-multiqc/2023-07-21--4-2-4/SBJ01147/",
//          "icav2://reference-data/dragen-wts-multiqc/2023-07-21--4-2-4/SBJ01620/",
//          "icav2://reference-data/dragen-wts-multiqc/2023-07-21--4-2-4/SBJ01286/",
//          "icav2://reference-data/dragen-wts-multiqc/2023-07-21--4-2-4/SBJ01673/"
//        ],
//        "cl_config_sample_names_replace": {
//            "PRJ220412": "Ref_1_Good",
//            "MDX210318": "Ref_2_Good",
//            "PRJ220466": "Ref_3_Good",
//            "PRJ211234": "Ref_4_Bad",
//            "PRJ220790": "Ref_5_Bad",
//            "L2200121_dragen_qualimap": "Ref_1_Good",
//            "L2101521_dragen_qualimap": "Ref_2_Good",
//            "L2200188_dragen_qualimap": "Ref_3_Good",
//            "L2101763_dragen_qualimap": "Ref_4_Bad",
//            "L2200311_dragen_qualimap": "Ref_5_Bad"
//        }
//    }
//  ]'
export const icav2WtsQcReferenceSamplesUriMappingSSMParameterPath =
  '/icav2/umccr-prod/wts_qc_reference_samples';

/*
Resources generated by the WTS Stateful Stack
*/
export const wtsIcav2PipelineManagerSSMRoot = '/orcabus/wts';

// Stateful
export const wtsIcav2PipelineManagerDynamodbTableName = 'wtsICAv2AnalysesDynamoDBTable';
export const wtsDynamoDbTableSSMName = path.join(
  wtsIcav2PipelineManagerSSMRoot,
  'dynamodb_table_name'
);
export const wtsDynamoDbTableSSMArn = path.join(
  wtsIcav2PipelineManagerSSMRoot,
  'dynamodb_table_arn'
);

/*
WTS Stateless stack
*/

// Deployed under dev/stg/prod
export const wtsIcav2PipelineIdSSMParameterPath = '/icav2/umccr-prod/wts_4.2.4_pipeline_id'; // 1e53ae07-08a6-458b-9fa3-9cf7430409a0
export const wtsIcav2PipelineWorkflowType = 'wts';
export const wtsIcav2PipelineWorkflowTypeVersion = '4.2.4';
export const wtsIcav2ServiceVersion = '2024.07.01';
export const wtsIcav2ReadyEventSource = 'orcabus.workflowmanager';
export const wtsIcav2EventSource = 'orcabus.wts';
export const wtsIcav2EventDetailType = 'WorkflowRunStateChange';
export const wtsStateMachinePrefix = 'wtsSfn';
export const wtsDefaultDragenReferenceVersion = 'v9-r3';

export const wtsDefaultGencodeAnnotationVersion = 'v39';

export const wtsDefaultFastaReferenceVersion = 'hg38';

export const wtsDefaultArribaVersion = '2.4.0';

export const wtsDefaultQcReferenceSamplesVersion = '2023-07-21--4.2.4';

/*
Resources required by the umccrise stacks
*/

// Deployed under dev/stg/prod
// '
//   [
//     {
//       "name": "202303",
//       "uri": "icav2://reference-data/umccrise/202303/genomes.tar.gz"
//     }
//   ]
// '
export const icav2UmccriseGenomesReferenceUriMappingSSMParameterPath =
  '/icav2/umccr-prod/umccrise_genomes_reference_mapping'; //

/*
Resources generated by the UMCCRise Stateful Stack
*/
export const umccriseIcav2PipelineManagerSSMRoot = '/orcabus/umccrise';

/*
UMCCRise Stateful stack
*/
export const umccriseIcav2PipelineManagerDynamodbTableName = 'umccriseICAv2AnalysesDynamoDBTable';
export const umccriseDynamoDbTableSSMName = path.join(
  umccriseIcav2PipelineManagerSSMRoot,
  'dynamodb_table_name'
);
export const umccriseDynamoDbTableSSMArn = path.join(
  umccriseIcav2PipelineManagerSSMRoot,
  'dynamodb_table_arn'
);

/*
UMCCRise Stateless stack
*/

// Deployed in dev/stg/prod
export const umccriseIcav2PipelineIdSSMParameterPath =
  '/icav2/umccr-prod/umccrise_2.3.1_pipeline_id'; // 61254f38-b56e-4576-a8a1-341e5c412d11
export const umccriseIcav2PipelineWorkflowType = 'umccrise';
export const umccriseIcav2PipelineWorkflowTypeVersion = '2.3.1';
export const umccriseIcav2ServiceVersion = '2024.07.01';
export const umccriseIcav2ReadyEventSource = 'orcabus.workflowmanager';
export const umccriseIcav2EventSource = 'orcabus.umccrise';
export const umccriseIcav2EventDetailType = 'WorkflowRunStateChange';
export const umccriseStateMachinePrefix = 'umccriseSfn';
export const umccriseDefaultGenomeVersion = '202303';

/*
Resources generated by the Rnasum Stateful Stack
*/
export const rnasumIcav2PipelineManagerSSMRoot = '/orcabus/rnasum';

/*
Rnasum Stateful stack
*/
export const rnasumIcav2PipelineManagerDynamodbTableName = 'rnasumICAv2AnalysesDynamoDBTable';
export const rnasumDynamoDbTableSSMName = path.join(
  rnasumIcav2PipelineManagerSSMRoot,
  'dynamodb_table_name'
);
export const rnasumDynamoDbTableSSMArn = path.join(
  rnasumIcav2PipelineManagerSSMRoot,
  'dynamodb_table_arn'
);

/*
UMCCRise Stateless stack
*/

// Deployed in dev/stg/prod
export const rnasumIcav2PipelineIdSSMParameterPath = '/icav2/umccr-prod/rnasum_1.1.5_pipeline_id'; // c412a2ee-5a92-465d-b619-7516da56b9bf
export const rnasumIcav2PipelineWorkflowType = 'rnasum';
export const rnasumIcav2PipelineVersion = '1.1.5';
export const rnasumIcav2ServiceVersion = '2024.07.01';
export const rnasumIcav2ReadyEventSource = 'orcabus.workflowmanager';
export const rnasumIcav2EventSource = 'orcabus.rnasum';
export const rnasumIcav2EventDetailType = 'WorkflowRunStateChange';
export const rnasumStateMachinePrefix = 'rnasumSfn';
export const rnasumDefaultDatasetVersion = 'PANCAN';

/*
Ora Compression Stateless Stack
*/

// Deployed in dev
// export const oraCompressionTarSSMParameterPath = '/icav2/umccr-prod/ora_compression_tar_uri'; // icav2://reference-data/dragen-ora/v2/ora_reference_v2.tar.gz

/*
PierianDx Stateful and Stateless stacks
*/
export const pieriandxPrefix = 'pieriandx';
export const pieriandxTriggerLaunchSource = 'orcabus.workflowmanager';
export const pieriandxWorkflowName = 'pieriandx';
export const pieriandxWorkflowVersion = '2.1';
export const pieriandxDetailType = 'WorkflowRunStateChange';
export const pieriandxEventSource = 'orcabus.pieriandx';
export const pieriandxPayloadVersion = '2024.10.01';
export const pieriandxDynamodbTable = 'PierianDxPipelineDynamoDbTable';

/*
[
    {
        "panelName": "main",
        "panelId": "tso500_DRAGEN_ctDNA_v2_1_Universityofmelbourne"  // pragma: allowlist secret
    },
    {
        "panelName": "subpanel",
        "panelId": "tso500_DRAGEN_ctDNA_v2_1_subpanel_Universityofmelbourne"  // pragma: allowlist secret
    }
]

*/
export const pieriandxDefaultPanelName = 'main';
export const pieriandxPanelMapSsmParameterPath = '/umccr/orcabus/stateful/pieriandx/panel_map';

/*
[
    {
        "dagName": "cromwell_tso500_ctdna_workflow_1.0.4",
        "dagDescription": "tso500_ctdna_workflow"
    }
]
*/
export const pieriandxDefaultDagName = 'cromwell_tso500_ctdna_workflow_1.0.4';
export const pieriandxDagSsmParameterPath = '/umccr/orcabus/stateful/pieriandx/dag_map';

/*
"s3://pdx-cgwxfer-test/melbournetest" // development
"s3://pdx-cgwxfer-test/melbournetest" // staging
"s3://pdx-xfer/melbourne" // production
*/
export const pieriandxS3SequencerRunRootSsmParameterPath =
  '/umccr/orcabus/pieriandx/s3_sequencer_run_root';

/*
"services@umccr.org"  // development
"services@umccr.org"  // staging
"services@umccr.org"  // production
*/
export const pieriandxUserEmailSsmParameterPath = '/umccr/orcabus/pieriandx/user_email';

/*
"melbournetest"  // development
"melbournetest"  // staging
"melbourne" //  production
*/
export const pieriandxInstitutionSsmParameterPath = '/umccr/orcabus/pieriandx/institution';

/*
"https://app.uat.pieriandx.com/cgw-api/v2.0.0"  // development
"https://app.uat.pieriandx.com/cgw-api/v2.0.0"  // staging
"https://app.pieriandx.com/cgw-api/v2.0.0" //  production
*/
export const pieriandxBaseUrlSsmParameterPath = '/umccr/orcabus/pieriandx/base_url';

// Constant for all environments
export const pieriandxAuthTokeSsmParameterPath = 'collectPierianDxAccessToken';

// Secret name for PierianDx S3 credentials (test bucket for dev and staging, prod bucket for prod)
export const pieriandxS3CredentialsSecretsManagerId = 'PierianDx/S3Credentials'; // pragma: allowlist secret

/*
[
  {
    "project_id": "PO",
    "panel": "subpanel",
    "sample_type": "patientcare",
    "is_identified": "identified",
    "default_snomed_disease_code": null
  },
  {
    "project_id": "COUMN",
    "panel": "subpanel",
    "sample_type": "patientcare",
    "is_identified": "identified",
    "default_snomed_disease_code": null
  },
  {
    "project_id": "CUP",
    "panel": "main",
    "sample_type": "patientcare",
    "is_identified": "identified",
    "default_snomed_disease_code": 285645000
  },
  {
    "project_id": "PPGL",
    "panel": "main",
    "sample_type": "patientcare",
    "is_identified": "identified",
    "default_snomed_disease_code": null
  },
  {
    "project_id": "MESO",
    "panel": "subpanel",
    "sample_type": "patientcare",
    "is_identified": "identified",
    "default_snomed_disease_code": null
  },
  {
    "project_id": "OCEANiC",
    "panel": "subpanel",
    "sample_type": "patientcare",
    "is_identified": "deidentified",
    "default_snomed_disease_code": null
  },
  {
    "project_id": "SOLACE2",
    "panel": "main",
    "sample_type": "patientcare",
    "is_identified": "deidentified",
    "default_snomed_disease_code": 55342001
  },
  {
    "project_id": "IMPARP",
    "panel": "main",
    "sample_type": "patientcare",
    "is_identified": "deidentified",
    "default_snomed_disease_code": 55342001
  },
  {
    "project_id": "Control",
    "panel": "main",
    "sample_type": "validation",
    "is_identified": "deidentified",
    "default_snomed_disease_code": 55342001
  },
  {
    "project_id": "QAP",
    "panel": "subpanel",
    "sample_type": "patientcare",
    "is_identified": "identified",
    "default_snomed_disease_code": null
  },
  {
    "project_id": "iPredict2",
    "panel": "subpanel",
    "sample_type": "patientcare",
    "is_identified": "identified",
    "default_snomed_disease_code":null
  },
  {
    "project_id": "*",
    "panel": "main",
    "sample_type": "patientcare",
    "is_identified": "deidentified",
    "default_snomed_disease_code": 55342001
  }
]
*/
export const pieriandxProjectInfoSsmParameterPath = '/umccr/orcabus/pieriandx/project_info';

export const redcapLambdaFunctionName: Record<AppStage, string> = {
  [AppStage.BETA]: 'redcap-apis-dev-lambda-function',
  [AppStage.GAMMA]: 'redcap-apis-stg-lambda-function',
  [AppStage.PROD]: 'redcap-apis-prod-lambda-function',
};

/*
Resources generated by the Oncoanalyser Stateful Stack
*/
export const oncoanalyserNfPipelineManagerSSMRoot = '/orcabus/oncoanalyser';
export const oncoanalyserNfPipelineManagerDynamodbTableName = 'oncoanalyserNfAnalysesDynamoDBTable';
export const oncoanalyserNfDynamoDbTableSSMName = path.join(
  oncoanalyserNfPipelineManagerSSMRoot,
  'dynamodb_table_name'
);
export const oncoanalyserNfDynamoDbTableSSMArn = path.join(
  oncoanalyserNfPipelineManagerSSMRoot,
  'dynamodb_table_arn'
);

// Oncoanalyser stateless stack
export const oncoanalyserPipelineWorkflowTypePrefix = 'oncoanalyser';
export const oncoanalyserPipelineWorkflowTypeVersion = '1.0.0';
export const oncoanalyserServiceVersion = '2024.10.23';
export const oncoanalyserReadyEventSource = 'orcabus.workflowmanager';
export const oncoanalyserEventSource = 'orcabus.oncoanalysermanager';
export const oncoanalyserEventDetailType = 'WorkflowRunStateChange';

export const oncoanalyserBatchJobQueueArn: Record<AppStage, string> = {
  [AppStage.BETA]: `arn:aws:batch:${region}:${accountIdAlias.beta}:job-queue/nextflow-pipeline`, // pragma: allowlist secret
  [AppStage.GAMMA]: `arn:aws:batch:${region}:${accountIdAlias.gamma}:job-queue/nextflow-pipeline`, // pragma: allowlist secret
  [AppStage.PROD]: `arn:aws:batch:${region}:${accountIdAlias.prod}:job-queue/nextflow-pipeline`, // pragma: allowlist secret
};

export const oncoanalyserBatchJobDefinitionArn: Record<AppStage, string> = {
  [AppStage.BETA]: `arn:aws:batch:${region}:${accountIdAlias.beta}:job-definition/Nextflow-oncoanalyser`, // pragma: allowlist secret
  [AppStage.GAMMA]: `arn:aws:batch:${region}:${accountIdAlias.gamma}:job-definition/Nextflow-oncoanalyser`, // pragma: allowlist secret
  [AppStage.PROD]: `arn:aws:batch:${region}:${accountIdAlias.prod}:job-definition/Nextflow-oncoanalyser`, // pragma: allowlist secret
};
export const oncoanalyserStateMachinePrefix = 'oncoanalyser';

export const oncoanalyserPipelineVersionSSMParameterPath =
  '/nextflow_stack/oncoanalyser/pipeline_version_tag';

/*
Sash Stateful stack
*/
export const sashNfPipelineManagerSSMRoot = '/orcabus/sash';
export const sashNfPipelineManagerDynamodbTableName = 'sashNfAnalysesDynamoDBTable';
export const sashNfDynamoDbTableSSMName = path.join(
  sashNfPipelineManagerSSMRoot,
  'dynamodb_table_name'
);
export const sashNfDynamoDbTableSSMArn = path.join(
  sashNfPipelineManagerSSMRoot,
  'dynamodb_table_arn'
);

// Sash stack
export const sashPipelineWorkflowType = 'sash';
export const sashPipelineWorkflowTypeVersion = '1.0.0';
export const sashServiceVersion = '2024.10.23';
export const sashReadyEventSource = 'orcabus.workflowmanager';
export const sashEventSource = 'orcabus.sashmanager';
export const sashEventDetailType = 'WorkflowRunStateChange';

export const sashBatchJobQueueArn: Record<AppStage, string> = {
  [AppStage.BETA]: `arn:aws:batch:${region}:${accountIdAlias.beta}:job-queue/nextflow-pipeline`, // pragma: allowlist secret
  [AppStage.GAMMA]: `arn:aws:batch:${region}:${accountIdAlias.gamma}:job-queue/nextflow-pipeline`, // pragma: allowlist secret
  [AppStage.PROD]: `arn:aws:batch:${region}:${accountIdAlias.prod}:job-queue/nextflow-pipeline`, // pragma: allowlist secret
};
export const sashBatchJobDefinitionArn: Record<AppStage, string> = {
  [AppStage.BETA]: `arn:aws:batch:${region}:${accountIdAlias.beta}:job-definition/Nextflow-sash`, // pragma: allowlist secret
  [AppStage.GAMMA]: `arn:aws:batch:${region}:${accountIdAlias.gamma}:job-definition/Nextflow-sash`, // pragma: allowlist secret
  [AppStage.PROD]: `arn:aws:batch:${region}:${accountIdAlias.prod}:job-definition/Nextflow-sash`, // pragma: allowlist secret
};

export const sashStateMachinePrefix = 'sash';
export const sashPipelineVersionSSMParameterPath = '/nextflow_stack/sash/pipeline_version_tag';

// Stacky Stack
export const stackyEventBusName = eventBusName;
export const stackyInstrumentRunTableName = 'stacky-instrument-run-table';
export const stackyCttsov2InputGlueTableName = 'stacky-cttsov2-workflow-glue-table';
export const stackyWgtsQcGlueTableName = 'stacky-wgts-qc-glue-table';
export const stackyTnGlueTableName = 'stacky-tn-glue-table';
export const stackyWtsGlueTableName = 'stacky-wts-glue-table';
export const stackyUmccriseGlueTableName = 'stacky-umccrise-glue-table';
export const stackyRnasumGlueTableName = 'stacky-rnasum-glue-table';
export const stackyPierianDxGlueTableName = 'stacky-pieriandx-glue-table';
export const stackyOncoanalyserGlueTableName = 'stacky-oncoanalyser-glue-table';
export const stackyOncoanalyserBothSashGlueTableName = 'stacky-oncoanalyser-both-sash-glue-table';
export const stackyWorkflowManagerTableName = 'stacky-workflow-manager-table';

// dev
// {
//    "project_id":"ea19a3f5-ec7c-4940-a474-c31cd91dbad4",
//    "project_name": "development"
// }
// stg
// {
//   "project_id": "157b9e78-b2e1-45a7-bfcd-691159995f7c",
//   "project_name": "staging"
// }
// prod
// {
//   "project_id": "eba5c946-1677-441d-bbce-6a11baadecbb",
//   "project_name": "production"
// }
export const stackyIcav2ProjectIdSsmParameterName =
  '/orcabus/stacky/icav2_project_id_and_name_json';

// dev: s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/primary/__instrument_run_id__/__portal_run_id__/
// stg: s3://pipeline-stg-cache-503977275616-ap-southeast-2/byob-icav2/staging/primary/__instrument_run_id__/__portal_run_id__/
// prod: s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/primary/__instrument_run_id__/__portal_run_id__/
export const stackyPrimaryOutputUriSsmParameterName = '/orcabus/stacky/primary_output_uri';

// dev: s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/analysis/__workflow_name__/__portal_run_id__/
// stg: s3://pipeline-stg-cache-503977275616-ap-southeast-2/byob-icav2/staging/analysis/__workflow_name__/__portal_run_id__/
// prod: s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/analysis/__workflow_name__/__portal_run_id__/
export const stackyAnalysisOutputUriSsmParameterName = '/orcabus/stacky/analysis_output_uri';

// dev: s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/logs/__workflow_name__/__portal_run_id__/
// stg: s3://pipeline-stg-cache-503977275616-ap-southeast-2/byob-icav2/staging/logs/__workflow_name__/__portal_run_id__/
// prod: s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/logs/__workflow_name__/__portal_run_id__/
export const stackyAnalysisLogsUriSsmParameterName = '/orcabus/stacky/analysis_logs_uri';

// dev: s3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/cache/__workflow_name__/__portal_run_id__/
// stg: s3://pipeline-stg-cache-503977275616-ap-southeast-2/byob-icav2/staging/cache/__workflow_name__/__portal_run_id__/
// prod: s3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/cache/__workflow_name__/__portal_run_id__/
export const stackyAnalysisCacheUriSsmParameterName = '/orcabus/stacky/analysis_cache_uri';

/*
Resources generated by the ORA Compression pipeline
*/

export const oraCompressionSSMRoot = '/orcabus/ora_compression/';

export const oraCompressionIcav2PipelineManagerDynamodbTableName =
  'oraCompressionICAv2AnalysesDynamoDBTable';

// Stateful
export const oraCompressionDynamoDbTableSSMName = path.join(
  oraCompressionSSMRoot,
  'dynamodb_table_name'
);
export const oraCompressionDynamoDbTableSSMArn = path.join(
  oraCompressionSSMRoot,
  'dynamodb_table_arn'
);

// Stateless
export const oraCompressionIcav2PipelineWorkflowType = 'ora-compression';
export const oraCompressionIcav2PipelineWorkflowTypeVersion = '4.2.4--v2';
export const oraCompressionIcav2ServiceVersion = '2024.07.01';

export const oraCompressionIcav2ReadyEventSource = 'orcabus.workflowmanager';
export const oraCompressionIcav2EventSource = 'orcabus.oracompression';
export const oraCompressionIcav2EventDetailType = 'WorkflowRunStateChange';
export const oraCompressionStateMachinePrefix = 'oraCompressionSfn';

/*
Resources used by the ora compression pipeline
*/

// Release can be found here: https://github.com/umccr/cwl-ica/releases/tag/dragen-instrument-run-fastq-to-ora-pipeline%2F4.2.4__20241120224050
// Pipeline ID is: 5c1c2fa2-30dc-46ed-9e7f-dc4fefac77b6
// deployed to dev, stg and prod
export const oraCompressionIcav2PipelineIdSSMParameterPath =
  '/icav2/umccr-prod/ora_compression_pipeline_id'; // 0540fca4-cc40-45ac-88e2-d32df69c6954

// Default Reference Uri for compressing ORA files
// Reference URI is icav2://reference-data/dragen-ora/v2/ora_reference_v2.tar.gz
// deployed to dev, stg and prod
export const oraCompressionDefaultReferenceUriSSmParameterPath =
  '/icav2/umccr-prod/ora_compression_default_reference_version_uri';

/*
Resources generated by the ora decompression manager
*/
export const oraDecompressionIcav2ReadyEventSource = 'orcabus.workflowmanager';
export const oraDecompressionIcav2EventSource = 'orcabus.oradecompression';
export const oraDecompressionIcav2EventDetailType = 'FastqListRowDecompressed';
export const oraDecompressionStateMachinePrefix = 'oraDecompressionSfn';
