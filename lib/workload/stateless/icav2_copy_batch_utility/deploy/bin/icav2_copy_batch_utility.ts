#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { ICAv2CopyBatchUtilityStack } from '../lib/stacks/icav2_copy_batch_utility_stack';
import {
  ICAV2_COPY_BATCH_STATE_MACHINE_ARN_SSM_PARAMETER_PATH, ICAV2_COPY_BATCH_STATE_MACHINE_NAME_SSM_PARAMETER_PATH,
  ICAV2_COPY_SINGLE_STATE_MACHINE_ARN_SSM_PARAMETER_PATH, ICAV2_COPY_SINGLE_STATE_MACHINE_NAME_SSM_PARAMETER_PATH,
  ICAV2_TOKEN_SECRET_ID,
} from '../constants';

const app = new cdk.App();
new ICAv2CopyBatchUtilityStack(app, 'Icav2CopyBatchUtilityStack', {
  icav2_token_secret_id: ICAV2_TOKEN_SECRET_ID,
  icav2_copy_batch_state_machine_arn_ssm_parameter_path: ICAV2_COPY_BATCH_STATE_MACHINE_ARN_SSM_PARAMETER_PATH,
  icav2_copy_batch_state_machine_name_ssm_parameter_path: ICAV2_COPY_BATCH_STATE_MACHINE_NAME_SSM_PARAMETER_PATH,
  icav2_copy_single_state_machine_arn_ssm_parameter_path: ICAV2_COPY_SINGLE_STATE_MACHINE_ARN_SSM_PARAMETER_PATH,
  icav2_copy_single_state_machine_name_ssm_parameter_path: ICAV2_COPY_SINGLE_STATE_MACHINE_NAME_SSM_PARAMETER_PATH,
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
});