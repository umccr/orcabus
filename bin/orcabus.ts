#!/usr/bin/env node
/**
 * NOTE:
 * This is manual deploy of OrcaBus to a specified account.
 * Typically, everything should deploy through CodePipeline in automated way.
 * A condition when need using this manual deployment should only be
 * targeted to some isolated AWS account for dev or onboarding experimental purpose.
 */
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
  tags: {
    'umccr-org:Stack': 'OrcaBusSandboxApp',
    'umccr-org:Product': 'OrcaBus',
  },
};

const config = getEnvironmentConfig('beta');
if (!config) throw new Error('No Config');

const statefulStack = new OrcaBusStatefulStack(app, 'OrcaBusStatefulStack', {
  ...config.stackProps.orcaBusStatefulConfig,
  ...props,
});

new OrcaBusStatelessStack(app, 'OrcaBusStatelessStack', {
  eventSourceDependency: statefulStack.intoEventSourceDependency(),
  ...config.stackProps.orcaBusStatelessConfig,
  ...props,
});
