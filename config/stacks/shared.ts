import { AuroraPostgresEngineVersion } from 'aws-cdk-lib/aws-rds';
import { ConfigurableDatabaseProps } from '../../lib/workload/stateful/stacks/shared/constructs/database';
import { SharedStackProps } from '../../lib/workload/stateful/stacks/shared/stack';
import {
  accountIdAlias,
  AppStage,
  computeSecurityGroupName,
  databasePort,
  dataSchemaRegistryName,
  dbClusterEndpointHostParameterName,
  dbClusterIdentifier,
  dbClusterResourceIdParameterName,
  eventBusName,
  eventDlqNameFMAnnotator,
  eventSchemaRegistryName,
  eventSourceQueueName,
  icav2ArchiveAnalysisBucket,
  icav2ArchiveFastqBucket,
  icav2PipelineCacheBucket,
  oncoanalyserBucket,
  rdsMasterSecretName,
  vpcProps,
} from '../constants';
import { Duration, RemovalPolicy } from 'aws-cdk-lib';
import { SchemaRegistryProps } from '../../lib/workload/stateful/stacks/shared/constructs/schema-registry';
import {
  EventBusArchiverProps,
  EventBusProps,
} from '../../lib/workload/stateful/stacks/shared/constructs/event-bus';
import { ComputeProps } from '../../lib/workload/stateful/stacks/shared/constructs/compute';
import { EventSourceProps } from '../../lib/workload/stateful/stacks/shared/constructs/event-source';
import { EventDLQProps } from '../../lib/workload/stateful/stacks/shared/constructs/event-dlq';

const getEventSchemaRegistryConstructProps = (): SchemaRegistryProps => {
  return {
    registryName: eventSchemaRegistryName,
    description: 'Schema Registry for ' + eventSchemaRegistryName,
  };
};

const getDataSchemaRegistryConstructProps = (): SchemaRegistryProps => {
  return {
    registryName: dataSchemaRegistryName,
    description: 'Schema Registry for ' + dataSchemaRegistryName,
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

export const eventSourcePattern = () => {
  return {
    $or: [
      {
        size: [{ numeric: ['>', 0] }],
      },
      {
        key: [{ 'anything-but': { wildcard: ['*/'] } }],
      },
    ],
  };
};

export const eventSourcePatternCache = () => {
  // NOT KEY in cache AND (SIZE > 0 OR NOT KEY ends with "/") expands to
  // (NOT KEY in cache and SIZE > 0) OR (NOT KEY in cache and NOT KEY ends with "/")\
  return {
    $or: [
      {
        key: [{ 'anything-but': { wildcard: ['byob-icav2/*/cache/*'] } }],
        size: [{ numeric: ['>', 0] }],
      },
      {
        key: [{ 'anything-but': { wildcard: ['byob-icav2/*/cache/*', '*/'] } }],
      },
    ],
  };
};

export const getEventSourceConstructProps = (stage: AppStage): EventSourceProps => {
  const eventTypes = [
    'Object Created',
    'Object Deleted',
    'Object Restore Completed',
    'Object Restore Expired',
    'Object Storage Class Changed',
    'Object Access Tier Changed',
  ];

  const props = {
    queueName: eventSourceQueueName,
    maxReceiveCount: 3,
    rules: [
      {
        bucket: oncoanalyserBucket[stage],
        eventTypes,
        patterns: eventSourcePattern(),
      },
      {
        bucket: icav2PipelineCacheBucket[stage],
        eventTypes,
        patterns: eventSourcePatternCache(),
      },
    ],
  };

  if (stage === AppStage.PROD) {
    props.rules.push({
      bucket: icav2ArchiveAnalysisBucket[stage],
      eventTypes,
      patterns: eventSourcePattern(),
    });
    props.rules.push({
      bucket: icav2ArchiveFastqBucket[stage],
      eventTypes,
      patterns: eventSourcePattern(),
    });
  }

  return props;
};

const getEventDLQConstructProps = (): EventDLQProps[] => {
  return [
    {
      queueName: eventDlqNameFMAnnotator,
      alarmName: 'Orcabus FMAnnotator DLQ Alarm',
    },
  ];
};

const getDatabaseConstructProps = (stage: AppStage): ConfigurableDatabaseProps => {
  const baseConfig = {
    clusterIdentifier: dbClusterIdentifier,
    defaultDatabaseName: 'orcabus',
    version: AuroraPostgresEngineVersion.VER_16_6,
    parameterGroupName: 'default.aurora-postgresql16',
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
        backupRetention: Duration.days(1),
        createT2BackupRetention: false,
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
        backupRetention: Duration.days(1),
        createT2BackupRetention: false,
      };
    case AppStage.PROD:
      return {
        ...baseConfig,
        numberOfInstance: 1,
        minACU: 0.5,
        maxACU: 16,
        enhancedMonitoringInterval: Duration.seconds(60),
        enablePerformanceInsights: true,
        removalPolicy: RemovalPolicy.RETAIN,
        backupRetention: Duration.days(7),
        createT2BackupRetention: true,
      };
  }
};

export const getSharedStackProps = (stage: AppStage): SharedStackProps => {
  return {
    vpcProps,
    eventSchemaRegistryProps: getEventSchemaRegistryConstructProps(),
    dataSchemaRegistryProps: getDataSchemaRegistryConstructProps(),
    eventBusProps: getEventBusConstructProps(stage),
    databaseProps: getDatabaseConstructProps(stage),
    computeProps: getComputeConstructProps(),
    eventSourceProps: getEventSourceConstructProps(stage),
    eventDLQProps: getEventDLQConstructProps(),
  };
};
