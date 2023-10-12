#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { MetadataManagerStack } from '../lib/metadataManagerStack';

// tags for our stacks
const tags = {
  'umccr-org:Stack': 'orcabusMetadataManager',
};

const description = 'MetadataManager for OrcaBus';

const app = new cdk.App();
new MetadataManagerStack(app, 'MetadataManagerStack', {
  // deploy this infrastructure to dev
  env: {
    account: '843407916570',
    region: 'ap-southeast-2',
  },
  tags: tags,
  description: description,
  network: {
    vpcName: 'main-vpc',
  },
  // Ideally this should be reusable RDS across the orcabus microservices
  database: {
    name: 'database',
    adminUser: 'orcabus_admin',
    enableMonitoring: {
      cloudwatchLogsExports: ['postgresql'],
      enablePerformanceInsights: true,
      monitoringInterval: cdk.Duration.seconds(60),
    },
    makePubliclyReachable: false,
    destroyOnRemove: true,
  },
  edgeDb: {
    secretPrefix: 'orcabusMetadataManager', // pragma: allowlist secret
    version: '3.2',
    makePubliclyReachable: {
      urlPrefix: 'orcabus-metadata-manager-edge-db',
    },
  },
});
