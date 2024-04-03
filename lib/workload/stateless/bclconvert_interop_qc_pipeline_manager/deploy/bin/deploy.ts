#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { BclconvertInteropQcPipelineLaunchStateMachineStack } from '../lib/stacks/bclconvert_interop_qc_pipeline_manager_stack';
import {
  BCLCONVERT_INTEROP_QC_PIPELINE_LAUNCH_STATE_MACHINE_ARN_SSM_PARAMETER_PATH,
  DYNAMODB_TABLE_NAME_SSM_PARAMETER_PATH, ICAV2_ACCESS_TOKEN_SECRET_ID,
  PIPELINE_ID_SSM_PARAMETER_PATH,
} from '../constants';

const app = new cdk.App();

// service-trial-user / umccr-development
new BclconvertInteropQcPipelineLaunchStateMachineStack(app, 'BclconvertInteropQcPipeline', {
  dynamodb_name_ssm_parameter_path: DYNAMODB_TABLE_NAME_SSM_PARAMETER_PATH,
  icav2_token_secret_id: ICAV2_ACCESS_TOKEN_SECRET_ID,
  bclconvert_interop_qc_launch_state_machine_ssm_parameter_path: BCLCONVERT_INTEROP_QC_PIPELINE_LAUNCH_STATE_MACHINE_ARN_SSM_PARAMETER_PATH,
  ssm_parameter_list: [
    PIPELINE_ID_SSM_PARAMETER_PATH
  ],
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION
  }
});