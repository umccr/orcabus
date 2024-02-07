#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { ICAv2CopyBatchStateMachineStack } from '../lib/stacks/icav2_copy_batch_stack';
import {
  COPY_BATCH_STATE_MACHINE_ARN_SSM_PARAMETER_PATH,
  ICAV2_JWT_SECRET_ARN_SSM_PARAMETER_PATH,
  SSM_PARAMETER_LIST_FOR_WORKFLOW_MANAGER,
} from '../constants';
import { ICAv2BCLConvertSuccessEventStateMachineStack } from '../lib/stacks/icav2_bclconvert_success_event_batch_stack';

const app = new cdk.App();

const icav2_copy_batch_state_machine_stack = new ICAv2CopyBatchStateMachineStack(app, 'ICAv2CopyBatchStateMachineStack', {
  icav2_jwt_ssm_parameter_path: ICAV2_JWT_SECRET_ARN_SSM_PARAMETER_PATH,
  icav2_copy_batch_state_machine_ssm_parameter_path: COPY_BATCH_STATE_MACHINE_ARN_SSM_PARAMETER_PATH,
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION
  },
});

const icav2_bclconvert_success_event_state_machine_stack = new ICAv2BCLConvertSuccessEventStateMachineStack(app, 'ICAv2BCLConvertSuccessEventStateMachineStack', {
  icav2_jwt_ssm_parameter_path: ICAV2_JWT_SECRET_ARN_SSM_PARAMETER_PATH,
  ssm_parameter_list: SSM_PARAMETER_LIST_FOR_WORKFLOW_MANAGER,
  icav2_copy_batch_state_machine_ssm_parameter_path: icav2_copy_batch_state_machine_stack.icav2_copy_batch_state_machine_ssm_parameter_path,
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION
  },
});