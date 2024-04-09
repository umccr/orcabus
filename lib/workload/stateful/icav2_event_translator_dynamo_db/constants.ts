const ROOT_SSM_PARAMETER_PATH = '/umccr/orcabus/stateful/icav2_event_translator_dynamo_db';

// ARN and NAME params
export const DYNAMODB_TABLE_ARN_SSM_PARAMETER_PATH = `${ROOT_SSM_PARAMETER_PATH}/translator_table_arn`;
export const DYNAMODB_TABLE_NAME_SSM_PARAMETER_PATH = `${ROOT_SSM_PARAMETER_PATH}/translator_table_name`;

export const DYNAMODB_TABLE_NAME = 'ICAv2EventTranslatorDynamoDBTable';
