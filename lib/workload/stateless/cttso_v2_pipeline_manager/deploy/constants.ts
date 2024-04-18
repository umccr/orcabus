
const STATEFUL_ROOT_SSM_PARAMETER_PATH = "/umccr/orcabus/stateful/cttso_v2_pipeline_dynamo_db";
export const DYNAMODB_TABLE_ARN_SSM_PARAMETER_PATH = `${STATEFUL_ROOT_SSM_PARAMETER_PATH}/analysis_table_arn`;
export const DYNAMODB_TABLE_NAME_SSM_PARAMETER_PATH = `${STATEFUL_ROOT_SSM_PARAMETER_PATH}/analysis_table_name`;

export const ICAV2_ACCESS_TOKEN_SECRET_ID = "ICAv2Jwticav2-credentials-umccr-service-user-trial"
export const ICAV2_COPY_BATCH_UTILITY_STATE_MACHINE_NAME_SSM_PARAMETER_PATH = "/icav2_copy_batch_utility/state_machine_name_batch"
export const PIPELINE_ID_SSM_PARAMETER_PATH = "/icav2/umccr-prod/tso500_ctdna_2.1_pipeline_id"
export const CTTSO_V2_LAUNCH_STATE_MACHINE_ARN_SSM_PARAMETER_PATH = "/icav2/umccr-prod/cttso_launch_state_machine_arn"
export const CTTSO_V2_LAUNCH_STATE_MACHINE_NAME_SSM_PARAMETER_PATH = "/icav2/umccr-prod/cttso_launch_state_machine_name"
export const ORCABUS_EVENT_NAME = "OrcaBusMain"

export const SSM_PARAMETER_LIST_FOR_CTTSO_LAUNCH_LAMBDAS = [
    PIPELINE_ID_SSM_PARAMETER_PATH
]