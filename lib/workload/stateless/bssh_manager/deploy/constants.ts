export const ICAV2_JWT_SECRET_ARN_SSM_PARAMETER_PATH = "/icav2/umccr-prod/service-user-trial-jwt-token-secret-arn"

export const BSSH_MANAGER_LAMBDA_LAYER_SSM_PARAMTER_PATH = "/bssh_manager/lambda/bssh_manager_tools_lambda_layer_arn"
export const COPY_BATCH_STATE_MACHINE_ARN_SSM_PARAMETER_PATH= "/bssh_manager/state_machine/copy_batch_state_machine_arn"

export const SSM_PARAMETER_LIST_FOR_WORKFLOW_MANAGER = [
    "/icav2/umccr-prod/cache_project_id",
    "/icav2/umccr-prod/cache_project_bclconvert_output_path",
    "/icav2/umccr-prod/cache_project_cttso_fastq_path"
]