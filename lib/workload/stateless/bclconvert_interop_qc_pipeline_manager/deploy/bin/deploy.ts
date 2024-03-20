#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { BclconvertInteropQcPipelineLaunchStateMachineStack } from '../lib/stacks/bclconvert_interop_qc_pipeline_manager_stack';
import {
  BCLCONVERT_INTEROP_QC_PIPELINE_LAUNCH_STATE_MACHINE_ARN_SSM_PARAMETER_PATH, DYNAMODB_ARN_SSM_PARAMETER_PATH,
  ICAV2_JWT_SECRET_ARN_SSM_PARAMETER_PATH, PIPELINE_ID_SSM_PARAMETER_PATH,
} from '../constants';

const app = new cdk.App();
new BclconvertInteropQcPipelineLaunchStateMachineStack(app, 'BclconvertInteropQcPipeline', {

  /* If you don't specify 'env', this stack will be environment-agnostic.
   * Account/Region-dependent features and context lookups will not work,
   * but a single synthesized template can be deployed anywhere. */

  /* Uncomment the next line to specialize this stack for the AWS Account
   * and Region that are implied by the current CLI configuration. */
  // env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },

  /* Uncomment the next line if you know exactly what Account and Region you
   * want to deploy the stack to. */
  // env: { account: '123456789012', region: 'us-east-1' },

  /* For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html */
  icav2_jwt_ssm_parameter_path: ICAV2_JWT_SECRET_ARN_SSM_PARAMETER_PATH,
  bclconvert_interop_qc_launch_state_machine_ssm_parameter_path: BCLCONVERT_INTEROP_QC_PIPELINE_LAUNCH_STATE_MACHINE_ARN_SSM_PARAMETER_PATH,
  interop_qc_pipeline_dynamodb_ssm_parameter_path: DYNAMODB_ARN_SSM_PARAMETER_PATH,
  ssm_parameter_list: [
    PIPELINE_ID_SSM_PARAMETER_PATH
  ],
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION
  }

});