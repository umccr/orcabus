#!/usr/bin/env node
import 'source-map-support/register';

import * as cdk from 'aws-cdk-lib';
import { StatelessPipelineStack } from '../lib/pipeline/orcabus-stateless-pipeline-stack';

const AWS_TOOLCHAIN_ACCOUNT = '383856791668'; // Bastion
const AWS_TOOLCHAIN_REGION = 'ap-southeast-2';

const app = new cdk.App();

new StatelessPipelineStack(app, `OrcaBusStatelessPipeline`, {
  env: {
    account: AWS_TOOLCHAIN_ACCOUNT,
    region: AWS_TOOLCHAIN_REGION,
  },
  tags: {
    'umccr-org:Stack': 'OrcaBusStatelessPipeline',
    'umccr-org:Product': 'OrcaBus',
  },
});
