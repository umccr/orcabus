#!/usr/bin/env node
import 'source-map-support/register';

import * as cdk from 'aws-cdk-lib';
import { PipelineStack } from '../lib/pipeline/orcabus-pipeline-stack';

// TODO: Change to proper Toolchain Acc Num (Currently this belongs to dev)
const AWS_TOOLCHAIN_ACCOUNT = '843407916570';
const AWS_TOOLCHAIN_REGION = 'ap-southeast-2';

const app = new cdk.App();

new PipelineStack(app, `OrcabusPipeline`, {
  env: {
    account: AWS_TOOLCHAIN_ACCOUNT,
    region: AWS_TOOLCHAIN_REGION,
  },
  tags: {
    'umccr.org:stack': 'orcabus',
  },
});
