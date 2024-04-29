import { AuroraPostgresEngineVersion } from 'aws-cdk-lib/aws-rds';
import { ConfigurableDatabaseProps } from '../../lib/workload/stateful/stacks/shared/constructs/database';
import { SharedStackProps } from '../../lib/workload/stateful/stacks/shared/stack';
import {
  AppStage,
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
  archiveBucketName,
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

const getEventBusConstructProps = (): EventBusProps => {
  return {
    eventBusName: eventBusName,
    archiveName: 'OrcaBusMainArchive',
    archiveDescription: 'OrcaBus main event bus archive',
    archiveRetention: 365,

    // add custom event archiver
    addCustomEventArchiver: true,
    vpcProps: vpcProps,
    lambdaSecurityGroupName: archiveSecurityGroupName,
    archiveBucketName: archiveBucketName,
  };
};

const getComputeConstructProps = (): ComputeProps => {
  return {
    securityGroupName: computeSecurityGroupName,
  };
};

const getEventSourceConstructProps = (stage: AppStage): EventSourceProps => {
  switch (stage) {
    case AppStage.BETA:
      return {
        queueName: eventSourceQueueName,
        maxReceiveCount: 3,
        rules: [
          {
            bucket: devBucket,
          },
        ],
      };
    case AppStage.GAMMA:
      return {
        queueName: eventSourceQueueName,
        maxReceiveCount: 3,
        rules: [
          {
            bucket: stgBucket,
          },
        ],
      };
    case AppStage.PROD:
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

const getDatabaseConstructProps = (stage: AppStage): ConfigurableDatabaseProps => {
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

  switch (stage) {
    case AppStage.BETA:
      return {
        ...baseConfig,
        numberOfInstance: 1,
        minACU: 0.5,
        maxACU: 16,
        enhancedMonitoringInterval: Duration.seconds(60),
        enablePerformanceInsights: true,
        removalPolicy: RemovalPolicy.DESTROY,
      };
    case AppStage.GAMMA:
      return {
        ...baseConfig,
        numberOfInstance: 1,
        minACU: 0.5,
        maxACU: 16,
        enhancedMonitoringInterval: Duration.seconds(60),
        enablePerformanceInsights: true,
        removalPolicy: RemovalPolicy.DESTROY,
      };
    case AppStage.PROD:
      return {
        ...baseConfig,
        numberOfInstance: 1,
        minACU: 0.5,
        maxACU: 16,
        removalPolicy: RemovalPolicy.RETAIN,
      };
  }
};

export const getSharedStackProps = (stage: AppStage): SharedStackProps => {
  return {
    vpcProps,
    schemaRegistryProps: getSchemaRegistryConstructProps(),
    eventBusProps: getEventBusConstructProps(),
    databaseProps: getDatabaseConstructProps(stage),
    computeProps: getComputeConstructProps(),
    eventSourceProps: getEventSourceConstructProps(stage),
  };
};
