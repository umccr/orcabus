
export const DYNAMODB_ARN_SSM_PARAMETER_PATH = "/umccr/orcabus/stateful/cttso_v2_pipeline_dynamo_db/analysis_table_arn"

export const CTTSO_CACHE_ROOT_SSM_PARAMETER_PATH = "/icav2/umccr-prod/cache_project_cttso_fastq_path"
export const CTTSO_OUTPUT_ROOT_SSM_PARAMETER_PATH = "/icav2/umccr-prod/output_project_cttso_fastq_path"

export const ICAV2_JWT_SECRET_ARN_SSM_PARAMETER_PATH = "/icav2/umccr-prod/service-user-trial-jwt-token-secret-arn"
export const ICAV2_COPY_BATCH_UTILITY_STATE_MACHINE_ARN_SSM_PARAMETER_PATH = "/icav2_copy_batch_utility/state_machine_arn"
export const PIPELINE_ID_SSM_PARAMETER_PATH = "/icav2/umccr-prod/tso500_ctdna_2.1_pipeline_id"


export const SSM_PARAMETER_LIST_FOR_CTTSO_LAUNCH_LAMBDAS = [
    CTTSO_CACHE_ROOT_SSM_PARAMETER_PATH,
    CTTSO_OUTPUT_ROOT_SSM_PARAMETER_PATH,
    ICAV2_JWT_SECRET_ARN_SSM_PARAMETER_PATH,
    PIPELINE_ID_SSM_PARAMETER_PATH
]