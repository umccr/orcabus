import { AuroraPostgresEngineVersion } from 'aws-cdk-lib/aws-rds';
import { ConfigurableDatabaseProps } from '../../lib/workload/stateful/stacks/shared/constructs/database';
import { SharedStackProps } from '../../lib/workload/stateful/stacks/shared/stack';
import {
  AppStage,
  accountIdAlias,
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
} from '../constants';
import { Duration, RemovalPolicy } from 'aws-cdk-lib';
import { SchemaRegistryProps } from '../../lib/workload/stateful/stacks/shared/constructs/schema-registry';
import {
  EventBusProps,
  EventBusArchiverProps,
} from '../../lib/workload/stateful/stacks/shared/constructs/event-bus';
import { ComputeProps } from '../../lib/workload/stateful/stacks/shared/constructs/compute';
import { EventSourceProps } from '../../lib/workload/stateful/stacks/shared/constructs/event-source';

const getSchemaRegistryConstructProps = (): SchemaRegistryProps => {
  return {
    registryName: regName,
    description: 'Registry for OrcaBus Events',
  };
};

const getEventBusConstructProps = (stage: AppStage): EventBusProps => {
  const baseConfig = {
    eventBusName: eventBusName,
    archiveName: 'OrcaBusMainArchive',
    archiveDescription: 'OrcaBus main event bus archive',
    archiveRetention: 365,
  };

  const baseUniversalEventArchiverProps: EventBusArchiverProps = {
    vpcProps: vpcProps,
    archiveBucketName: 'orcabus-universal-events-archive-' + accountIdAlias[stage],
    lambdaSecurityGroupName: 'OrcaBusSharedEventBusUniversalEventArchiveSecurityGroup',
    bucketRemovalPolicy: RemovalPolicy.DESTROY,
  };

  switch (stage) {
    case AppStage.BETA:
      return {
        ...baseConfig,
        addCustomEventArchiver: true,
        universalEventArchiverProps: baseUniversalEventArchiverProps,
      };
    case AppStage.GAMMA:
      return {
        ...baseConfig,
        addCustomEventArchiver: true,
        universalEventArchiverProps: baseUniversalEventArchiverProps,
      };
    case AppStage.PROD:
      return {
        ...baseConfig,
        addCustomEventArchiver: true,
        universalEventArchiverProps: {
          ...baseUniversalEventArchiverProps,
          bucketRemovalPolicy: RemovalPolicy.RETAIN,
        },
      };
  }
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
    eventBusProps: getEventBusConstructProps(stage),
    databaseProps: getDatabaseConstructProps(stage),
    computeProps: getComputeConstructProps(),
    eventSourceProps: getEventSourceConstructProps(stage),
  };
};
