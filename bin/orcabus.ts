#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { OrcaBusStatelessStack } from '../lib/workload/orcabus-stateless-stack';
import { OrcaBusStatefulStack } from '../lib/workload/orcabus-stateful-stack';

const app = new cdk.App();

new OrcaBusStatefulStack(app, 'OrcaBusStatefulStack', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
});

new OrcaBusStatelessStack(app, 'OrcaBusStatelessStack', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
});
