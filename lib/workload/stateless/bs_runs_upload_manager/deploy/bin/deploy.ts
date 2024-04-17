#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { BsRunsUploadManagerStack } from '../lib/stacks/bs_runs_upload_manager_stack';
import {
  BASESPACE_TOKEN_SECRET_ID,
  EVENTBUS_NAME,
  GDS_DEV_TEMP_PATH,
  ICA_TOKEN_SECRET_ID,
  PORTAL_TOKEN_SECRET_ID,
} from '../constants';

const app = new cdk.App();
new BsRunsUploadManagerStack(
    app,
    'BsRunsUploadManagerStack',
    {
      basespace_token_secret_id: BASESPACE_TOKEN_SECRET_ID, // BaseSpaceAccessTokenSecret
      eventbus_name: EVENTBUS_NAME, // OrcabusMain
      ica_token_secret_id: ICA_TOKEN_SECRET_ID,  // ICASecretsPortal
      portal_token_secret_id: PORTAL_TOKEN_SECRET_ID, // orcabus/token-service-jwt
      gds_system_files_path: GDS_DEV_TEMP_PATH, // gds://development/primary_data/temp/bs_runs_upload_tes/
      env: {
        account: process.env.CDK_DEFAULT_ACCOUNT,
        region: process.env.CDK_DEFAULT_REGION,
      }
    }
  )