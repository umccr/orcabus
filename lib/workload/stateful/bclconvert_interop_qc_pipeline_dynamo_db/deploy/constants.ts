const ROOT_SSM_PARAMETER_PATH = '/umccr/orcabus/stateful/bclconvert_interop_qc_pipeline_dynamo_db';

export const DYNAMODB_TABLE_ARN_SSM_PARAMETER_PATH = `${ROOT_SSM_PARAMETER_PATH}/analysis_table_arn`;
export const DYNAMODB_TABLE_NAME_SSM_PARAMETER_PATH = `${ROOT_SSM_PARAMETER_PATH}/analysis_table_name`;

export const DYNAMODB_TABLE_NAME = 'bclconvertInteropQcICAv2AnalysesDynamoDBTable'