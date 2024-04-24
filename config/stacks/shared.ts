import { AuroraPostgresEngineVersion } from 'aws-cdk-lib/aws-rds';
import { ConfigurableDatabaseProps } from '../../lib/workload/stateful/stacks/shared/constructs/database';
import { SharedStackProps } from '../../lib/workload/stateful/stacks/shared/stack';
import {
  AccountName,
  computeSecurityGroupName,
  databasePort,
  dbClusterEndpointHostParameterName,
  dbClusterIdentifier,
  dbClusterResourceIdParameterName,
  devBucket,
  eventBusName,
  eventSourceQueueName,
  prodBucket,
  rdsMasterSecretName,
  regName,
  stgBucket,
  vpcProps,
  archiveBucketNameSuffix,
  archiveSecurityGroupName,
} from '../constants';
import { Duration, RemovalPolicy } from 'aws-cdk-lib';
import { SchemaRegistryProps } from '../../lib/workload/stateful/stacks/shared/constructs/schema-registry';
import { EventBusProps } from '../../lib/workload/stateful/stacks/shared/constructs/event-bus';
import { ComputeProps } from '../../lib/workload/stateful/stacks/shared/constructs/compute';
import { EventSourceProps } from '../../lib/workload/stateful/stacks/shared/constructs/event-source';

const getSchemaRegistryConstructProps = (): SchemaRegistryProps => {
  return {
    registryName: regName,
    description: 'Registry for OrcaBus Events',
  };
};

const getEventBusConstructProps = (n: AccountName): EventBusProps => {
  const baseConfig = {
    eventBusName: eventBusName,
    archiveName: 'OrcaBusMainArchive',
    archiveDescription: 'OrcaBus main event bus archive',
    archiveRetention: 365,

    // common config for custom event archiver
    vpcProps: vpcProps,
    lambdaSecurityGroupName: archiveSecurityGroupName,
  };

  switch (n) {
    case 'beta':
      return {
        ...baseConfig,
        addCustomEventArchiver: true,
        archiveBucketName: 'umccr-dev-' + archiveBucketNameSuffix,
        enableBucketRetainPolicy: false,
      };
    case 'gamma':
      return {
        ...baseConfig,
        addCustomEventArchiver: true,
        archiveBucketName: 'umccr-stg-' + archiveBucketNameSuffix,
        enableBucketRetainPolicy: false,
      };
    case 'prod':
      return {
        ...baseConfig,
        addCustomEventArchiver: true,
        archiveBucketName: 'umccr-prod-' + archiveBucketNameSuffix,
        enableBucketRetainPolicy: true,
      };
  }
};

const getComputeConstructProps = (): ComputeProps => {
  return {
    securityGroupName: computeSecurityGroupName,
  };
};

const getEventSourceConstructProps = (n: AccountName): EventSourceProps => {
  switch (n) {
    case 'beta':
      return {
        queueName: eventSourceQueueName,
        maxReceiveCount: 3,
        rules: [
          {
            bucket: devBucket,
          },
        ],
      };
    case 'gamma':
      return {
        queueName: eventSourceQueueName,
        maxReceiveCount: 3,
        rules: [
          {
            bucket: stgBucket,
          },
        ],
      };
    case 'prod':
      return {
        queueName: eventSourceQueueName,
        maxReceiveCount: 3,
        rules: [
          {
            bucket: prodBucket,
          },
        ],
      };
  }
};

const getDatabaseConstructProps = (n: AccountName): ConfigurableDatabaseProps => {
  const baseConfig = {
    clusterIdentifier: dbClusterIdentifier,
    defaultDatabaseName: 'orcabus',
    version: AuroraPostgresEngineVersion.VER_15_4,
    parameterGroupName: 'default.aurora-postgresql15',
    username: 'postgres',
    dbPort: databasePort,
    masterSecretName: rdsMasterSecretName,
    clusterResourceIdParameterName: dbClusterResourceIdParameterName,
    clusterEndpointHostParameterName: dbClusterEndpointHostParameterName,
    secretRotationSchedule: Duration.days(7),
  };

  switch (n) {
    case 'beta':
      return {
        ...baseConfig,
        numberOfInstance: 1,
        minACU: 0.5,
        maxACU: 16,
        enhancedMonitoringInterval: Duration.seconds(60),
        enablePerformanceInsights: true,
        removalPolicy: RemovalPolicy.DESTROY,
      };
    case 'gamma':
      return {
        ...baseConfig,
        numberOfInstance: 1,
        minACU: 0.5,
        maxACU: 16,
        enhancedMonitoringInterval: Duration.seconds(60),
        enablePerformanceInsights: true,
        removalPolicy: RemovalPolicy.DESTROY,
      };
    case 'prod':
      return {
        ...baseConfig,
        numberOfInstance: 1,
        minACU: 0.5,
        maxACU: 16,
        removalPolicy: RemovalPolicy.RETAIN,
      };
  }
};

export const getSharedStackProps = (n: AccountName): SharedStackProps => {
  return {
    vpcProps,
    schemaRegistryProps: getSchemaRegistryConstructProps(),
    eventBusProps: getEventBusConstructProps(n),
    databaseProps: getDatabaseConstructProps(n),
    computeProps: getComputeConstructProps(),
    eventSourceProps: getEventSourceConstructProps(n),
  };
};
