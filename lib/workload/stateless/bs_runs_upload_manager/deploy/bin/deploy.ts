#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { BsRunsUploadManagerStack } from '../lib/stacks/bs_runs_upload_manager_stack';
import { GDS_DEV_TEMP_PATH, ICA_TOKEN_SECRET_ID } from '../constants';

const app = new cdk.App();
new BsRunsUploadManagerStack(
    app,
    'BsRunsUploadManagerStack',
    {
      ica_token_secret_id: ICA_TOKEN_SECRET_ID,  // ICASecretsPortal
      gds_system_files_path: GDS_DEV_TEMP_PATH, // gds://development/primary_data/temp/bs_runs_upload_tes/
      env: {
        account: process.env.CDK_DEFAULT_ACCOUNT,
        region: process.env.CDK_DEFAULT_REGION,
      }
    }
  )