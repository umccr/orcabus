#!/usr/bin/env node

import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { FilemanagerStack } from '../lib/filemanager_stack';
import { Tags } from 'aws-cdk-lib';

export const STACK_NAME = 'FilemanagerStack';
const STACK_DESCRIPTION = 'A stack deploying filemanager to dev.';

const app = new cdk.App();
new FilemanagerStack(
  app,
  STACK_NAME,
  {
    stackName: STACK_NAME,
    description: STACK_DESCRIPTION,
    tags: {
      Stack: STACK_NAME,
    },
    env: {
      region: 'ap-southeast-2',
    },
  },
  {
    destroyOnRemove: true,
    enableMonitoring: {
      enablePerformanceInsights: true,
    },
    public: [
      // Put your IP here if you want the database to be reachable.
    ],
    migrateDatabase: process.env.FILEMANAGER_DEPLOY_MIGRATE_DATABASE == 'true',
  }
);

Tags.of(app).add('Stack', STACK_NAME);