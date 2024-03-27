#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { ICAv2CopyBatchUtilityStack } from '../lib/stacks/icav2_copy_batch_utility_stack';
import { ICAV2_JWT_SECRET_ARN_SSM_PARAMETER_PATH, ICAV2_COPY_BATCH_STATE_MACHINE_ARN_SSM_PARAMETER_PATH } from '../constants';

const app = new cdk.App();
new ICAv2CopyBatchUtilityStack(app, 'Icav2CopyBatchUtilityStack', {
    icav2_jwt_ssm_parameter_path: ICAV2_JWT_SECRET_ARN_SSM_PARAMETER_PATH,
    icav2_copy_batch_state_machine_ssm_parameter_path: ICAV2_COPY_BATCH_STATE_MACHINE_ARN_SSM_PARAMETER_PATH,
    env: {
      account: process.env.CDK_DEFAULT_ACCOUNT,
      region: process.env.CDK_DEFAULT_REGION
    },
});