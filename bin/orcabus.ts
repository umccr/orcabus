#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { OrcaBusStatelessStack } from '../lib/workload/orcabus-stateless-stack';
import { OrcaBusStatefulStack } from '../lib/workload/orcabus-stateful-stack';
import { getEnvironmentConfig } from '../config/constants';

const app = new cdk.App();
const props: cdk.StackProps = {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
};

const config = getEnvironmentConfig('beta');
if (!config) throw new Error('No Config');

new OrcaBusStatefulStack(app, 'OrcaBusStatefulStack', {
  ...config.stackProps.orcaBusStatefulConfig,
  ...props,
});

new OrcaBusStatelessStack(app, 'OrcaBusStatelessStack', {
  ...config.stackProps.orcaBusStatelessConfig,
  ...props,
});
