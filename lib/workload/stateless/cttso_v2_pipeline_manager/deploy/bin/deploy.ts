#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { ctTSOV2LaunchStateMachineStack } from '../lib/stacks/cttso_v2_launch_stack';
import {
  CTTSO_V2_LAUNCH_STATE_MACHINE_ARN_SSM_PARAMETER_PATH,
  ICAV2_COPY_BATCH_UTILITY_STATE_MACHINE_ARN_SSM_PARAMETER_PATH,
  ICAV2_JWT_SECRET_ARN_SSM_PARAMETER_PATH,
  SSM_PARAMETER_LIST_FOR_CTTSO_LAUNCH_LAMBDAS,
} from '../constants';

const app = new cdk.App();
new ctTSOV2LaunchStateMachineStack(app, 'ctTSOv2LaunchStatemachineStack', {
  icav2_jwt_ssm_parameter_path: ICAV2_JWT_SECRET_ARN_SSM_PARAMETER_PATH,
  ssm_parameter_list: SSM_PARAMETER_LIST_FOR_CTTSO_LAUNCH_LAMBDAS,
  icav2_copy_batch_utility_state_machine_ssm_parameter_path: ICAV2_COPY_BATCH_UTILITY_STATE_MACHINE_ARN_SSM_PARAMETER_PATH,
  cttso_v2_launch_state_machine_ssm_parameter_path: CTTSO_V2_LAUNCH_STATE_MACHINE_ARN_SSM_PARAMETER_PATH,
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION
  },
});