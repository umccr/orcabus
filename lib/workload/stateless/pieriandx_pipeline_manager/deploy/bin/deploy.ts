#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { PieriandxLaunchStack } from '../lib/stacks/pieriandx_launch_stack';
import {
  DEV_ACCOUNT, DEV_REGION,
  DYNAMODB_SSM_PARAMETER_PATH_DEV,
  ICAV2_TOKEN_SECRET_ID_DEV,
  PIERIANDX_AUTH_TOKEN_COLLECT_TOKEN_LAMBDA_DEV,
  PIERIANDX_BASE_URL_DEV,
  PIERIANDX_INSTITUTION_DEV,
  PIERIANDX_LAUNCH_STATE_MACHINE_ARN_SSM_PARAMETER_PATH,
  PIERIANDX_LAUNCH_STATE_MACHINE_NAME_SSM_PARAMETER_PATH, PIERIANDX_S3_CREDENTIALS_SECRET_NAME,
  PIERIANDX_USER_EMAIL_DEV,
} from '../constants';

const app = new cdk.App();
new PieriandxLaunchStack(app, 'orcabusPieriandxDev', {
  dynamodb_table_ssm_parameter_path: DYNAMODB_SSM_PARAMETER_PATH_DEV,
  icav2_token_secret_id: ICAV2_TOKEN_SECRET_ID_DEV,
  pieriandx_auth_token_collection_lambda_name: PIERIANDX_AUTH_TOKEN_COLLECT_TOKEN_LAMBDA_DEV,
  pieriandx_base_url: PIERIANDX_BASE_URL_DEV,
  pieriandx_institution: PIERIANDX_INSTITUTION_DEV,
  pieriandx_launch_state_machine_arn_ssm_parameter_path: PIERIANDX_LAUNCH_STATE_MACHINE_ARN_SSM_PARAMETER_PATH,
  pieriandx_launch_state_machine_name_ssm_parameter_path: PIERIANDX_LAUNCH_STATE_MACHINE_NAME_SSM_PARAMETER_PATH,
  pieriandx_s3_access_token_secret_id: PIERIANDX_S3_CREDENTIALS_SECRET_NAME,
  pieriandx_user_email: PIERIANDX_USER_EMAIL_DEV,
  ssm_parameter_list: [],
  env: {
    account: DEV_ACCOUNT,
    region: DEV_REGION
  }
});