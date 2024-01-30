#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { WorkflowSessionStateMachineStack } from '../lib/workflow-session-state-machine-stack';
import {CopyBatchStateMachineStack} from "../lib/copy-batch-stack";
import {ICAV2_JWT_SECRET_ARN_SSM_PARAMETER_PATH} from "../constants";

const app = new cdk.App();
// new WorkflowSessionStateMachineStack(app, 'WorkflowSessionStateMachineStack', {
// });

new CopyBatchStateMachineStack(app, 'CopyBatchStateMachineStack', {
    icav2_jwt_ssm_parameter_path: ICAV2_JWT_SECRET_ARN_SSM_PARAMETER_PATH
});