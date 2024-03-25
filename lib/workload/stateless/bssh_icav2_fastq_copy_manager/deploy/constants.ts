export const ICAV2_JWT_SECRET_ARN_SSM_PARAMETER_PATH = "/icav2/umccr-prod/service-user-trial-jwt-token-secret-arn"

export const ICAV2_COPY_BATCH_UTILITY_STATE_MACHINE_ARN_SSM_PARAMETER_PATH = "/icav2_copy_batch_utility/state_machine_arn_batch"

export const BSSH_ICAV2_FASTQ_COPY_STATE_MACHINE_ARN_SSM_PARAMETER_PATH = "/bssh_icav2_fastq_copy/state_machine_arn"


export const SSM_PARAMETER_LIST_FOR_WORKFLOW_MANAGER = [
    "/icav2/umccr-prod/cache_project_id",
    "/icav2/umccr-prod/cache_project_bclconvert_output_path",
]