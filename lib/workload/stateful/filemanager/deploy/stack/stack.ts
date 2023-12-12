#!/usr/bin/env node

import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { FilemanagerStack } from './filemanager_stack';

export const STACK_NAME = 'FilemanagerStack';
const STACK_DESCRIPTION = 'A stack deploying filemanager to dev.';

const app = new cdk.App();
new FilemanagerStack(
  app,
  STACK_NAME,
  {
    account: process.env.CDK_DEPLOY_ACCOUNT || process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEPLOY_REGION || process.env.CDK_DEFAULT_REGION,
  },
  {
    database_url: 'postgresql://filemanager:filemanager@db:5432/filemanager', // pragma: allowlist secret
    force_path_style: true,
    stack_name: STACK_NAME,
    buildEnvironment: {
      // Override release profile to match defaults for dev builds.
      CARGO_PROFILE_RELEASE_OPT_LEVEL: '0',
      CARGO_PROFILE_RELEASE_DEBUG_ASSERTIONS: 'true',
      CARGO_PROFILE_RELEASE_OVERFLOW_CHECKS: 'true',
      CARGO_PROFILE_RELEASE_PANIC: 'unwind',
      CARGO_PROFILE_RELEASE_INCREMENTAL: 'true',
      CARGO_PROFILE_RELEASE_CODEGEN_UNITS: '256',

      // Additionally speed up builds by removing debug info. Please enable this if required.
      CARGO_PROFILE_RELEASE_DEBUG: 'false',
      // Add SCCACHE to speed up compilation. FIXME: Not cross-platform right now as it's defined here :/
      RUSTC_WRAPPER: '/opt/homebrew/bin/sccache',
    },
  },
  {
    stackName: STACK_NAME,
    description: STACK_DESCRIPTION,
    tags: {
      Stack: STACK_NAME,
    },
  }
);
