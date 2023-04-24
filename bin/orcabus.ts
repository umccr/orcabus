#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { OrcaBusStatelessStack, OrcaBusStatelessConfig } from '../lib/workload/orcabus-stateless-stack';
import { OrcaBusStatefulStack, OrcaBusStatefulConfig } from '../lib/workload/orcabus-stateful-stack';
import {MultiSchemaConstructProps} from "../lib/workload/stateless/schema/component";

const app = new cdk.App();

const regName : string = 'OrcaBusSchemaRegistry';

const sfConfig: OrcaBusStatefulConfig = {
  schemaRegistryProps: {
    registryName: regName,
    description: 'Registry for OrcaBus Events'
  }
}

const slConfig: OrcaBusStatelessConfig = {
  multiSchemaConstructProps: {
    registryName: regName,
    schemas: [
      {
        schemaName: 'BclConvertWorkflowRequest',
        schemaDescription: 'Request event for BclConvertWorkflow',
        schemaLocation: '../config/event_schemas/BclConvertWorkflowRequest.json'
      }
    ]
  },
}

const props: cdk.StackProps = {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION
  }
}


new OrcaBusStatefulStack(app, 'OrcaBusStatefulStack', {...props, ...sfConfig});

new OrcaBusStatelessStack(app, 'OrcaBusStatelessStack', {...props, ...slConfig});
