import { OrcaBusStatefulConfig } from '../lib/workload/orcabus-stateful-stack';
import { AuroraPostgresEngineVersion } from 'aws-cdk-lib/aws-rds';
import { OrcaBusStatelessConfig } from '../lib/workload/orcabus-stateless-stack';
import { Duration, RemovalPolicy } from 'aws-cdk-lib';
import { EventSourceProps } from '../lib/workload/stateful/event_source/component';
import { DbAuthType } from '../lib/workload/stateless/postgres_manager/function/type';
import {
  FILEMANAGER_SERVICE_NAME,
  FilemanagerConfig,
} from '../lib/workload/stateless/filemanager/deploy/lib/filemanager';

const regName = 'OrcaBusSchemaRegistry';
const eventBusName = 'OrcaBusMain';
const lambdaSecurityGroupName = 'OrcaBusLambdaSecurityGroup';
const dbClusterIdentifier = 'orcabus-db';
const dbClusterResourceIdParameterName = '/orcabus/db-cluster-resource-id';
const dbClusterEndpointHostParameterName = '/orcabus/db-cluster-endpoint-host';

const eventSourceQueueName = 'orcabus-event-source-queue';
const devBucket = 'umccr-temp-dev';
const stgBucket = 'umccr-temp-stg';
const prodBucket = 'org.umccr.data.oncoanalyser';

// Note, this should not end with a hyphen and 6 characters, otherwise secrets manager won't be
// able to find the secret using a partial ARN.
const rdsMasterSecretName = 'orcabus/master-rds'; // pragma: allowlist secret
const databasePort = 5432;

const orcaBusStatefulConfig = {
  schemaRegistryProps: {
    registryName: regName,
    description: 'Registry for OrcaBus Events',
  },
  eventBusProps: {
    eventBusName: eventBusName,
    archiveName: 'OrcaBusMainArchive',
    archiveDescription: 'OrcaBus main event bus archive',
    archiveRetention: 365,
  },
  databaseProps: {
    clusterIdentifier: dbClusterIdentifier,
    defaultDatabaseName: 'orcabus',
    version: AuroraPostgresEngineVersion.VER_15_4,
    parameterGroupName: 'default.aurora-postgresql15',
    username: 'postgres',
    dbPort: databasePort,
    masterSecretName: rdsMasterSecretName,
    monitoring: {
      cloudwatchLogsExports: ['orcabus-postgresql'],
    },
    clusterResourceIdParameterName: dbClusterResourceIdParameterName,
    clusterEndpointHostParameterName: dbClusterEndpointHostParameterName,
  },
  securityGroupProps: {
    securityGroupName: lambdaSecurityGroupName,
    securityGroupDescription: 'allow within same SecurityGroup and rds SG',
  },
};

const orcaBusStatelessConfig = {
  multiSchemaConstructProps: {
    registryName: regName,
    schemas: [
      {
        schemaName: 'BclConvertWorkflowRequest',
        schemaDescription: 'Request event for BclConvertWorkflow',
        schemaType: 'OpenApi3',
        schemaLocation: __dirname + '/event_schemas/BclConvertWorkflowRequest.json',
      },
      {
        schemaName: 'DragenWgsQcWorkflowRequest',
        schemaDescription: 'Request event for DragenWgsQcWorkflowRequest',
        schemaType: 'OpenApi3',
        schemaLocation: __dirname + '/event_schemas/DragenWgsQcWorkflowRequest.json',
      },
    ],
  },
  eventBusName: eventBusName,
  lambdaSecurityGroupName: lambdaSecurityGroupName,
  rdsMasterSecretName: rdsMasterSecretName,
  postgresManagerConfig: {
    masterSecretName: rdsMasterSecretName,
    dbClusterIdentifier: dbClusterIdentifier,
    clusterResourceIdParameterName: dbClusterResourceIdParameterName,
    microserviceDbConfig: [
      {
        name: 'sequence_run_manager',
        authType: DbAuthType.USERNAME_PASSWORD,
      },
      {
        name: 'metadata_manager',
        authType: DbAuthType.USERNAME_PASSWORD,
      },
      { name: FILEMANAGER_SERVICE_NAME, authType: DbAuthType.RDS_IAM },
    ],
  },
  metadataManagerConfig: {},
};

const eventSourceConfig = (bucket: string): EventSourceProps => {
  return {
    queueName: eventSourceQueueName,
    maxReceiveCount: 3,
    rules: [
      {
        bucket,
      },
    ],
  };
};

const filemanagerConfig = (bucket: string): FilemanagerConfig => {
  return {
    eventSourceQueueName: eventSourceQueueName,
    databaseClusterEndpointHostParameter:
      orcaBusStatefulConfig.databaseProps.clusterEndpointHostParameterName,
    port: databasePort,
    eventSourceBuckets: [bucket],
  };
};

interface EnvironmentConfig {
  name: string;
  accountId: string;
  stackProps: {
    orcaBusStatefulConfig: OrcaBusStatefulConfig;
    orcaBusStatelessConfig: OrcaBusStatelessConfig;
  };
}

/**
 * Validate the secret name so that it doesn't end with 6 characters and a hyphen.
 */
export const validateSecretName = (secretName: string) => {
  // If there are more config validation requirements like this it might be good to use
  // a dedicated library like zod.
  if (/-(.){6}$/.test(secretName)) {
    throw new Error('the secret name should not end with a hyphen and 6 characters');
  }
};

export const getEnvironmentConfig = (
  accountName: 'beta' | 'gamma' | 'prod'
): EnvironmentConfig | null => {
  let config = null;
  switch (accountName) {
    case 'beta':
      config = {
        name: 'beta',
        accountId: '843407916570', // umccr_development
        stackProps: {
          orcaBusStatefulConfig: {
            schemaRegistryProps: {
              ...orcaBusStatefulConfig.schemaRegistryProps,
            },
            eventBusProps: {
              ...orcaBusStatefulConfig.eventBusProps,
            },
            databaseProps: {
              ...orcaBusStatefulConfig.databaseProps,
              numberOfInstance: 1,
              minACU: 0.5,
              maxACU: 16,
              enhancedMonitoringInterval: Duration.seconds(60),
              enablePerformanceInsights: true,
              removalPolicy: RemovalPolicy.DESTROY,
            },
            securityGroupProps: {
              ...orcaBusStatefulConfig.securityGroupProps,
            },
            eventSourceProps: eventSourceConfig(devBucket),
          },
          orcaBusStatelessConfig: {
            ...orcaBusStatelessConfig,
            filemanagerConfig: filemanagerConfig(devBucket),
          },
        },
      };
      break;

    case 'gamma':
      config = {
        name: 'gamma',
        accountId: '455634345446', // umccr_staging
        stackProps: {
          orcaBusStatefulConfig: {
            schemaRegistryProps: {
              ...orcaBusStatefulConfig.schemaRegistryProps,
            },
            eventBusProps: {
              ...orcaBusStatefulConfig.eventBusProps,
            },
            databaseProps: {
              ...orcaBusStatefulConfig.databaseProps,
              numberOfInstance: 1,
              minACU: 0.5,
              maxACU: 16,
              enhancedMonitoringInterval: Duration.seconds(60),
              enablePerformanceInsights: true,
              removalPolicy: RemovalPolicy.DESTROY,
            },
            securityGroupProps: {
              ...orcaBusStatefulConfig.securityGroupProps,
            },
            eventSourceProps: eventSourceConfig(stgBucket),
          },
          orcaBusStatelessConfig: {
            ...orcaBusStatelessConfig,
            filemanagerConfig: filemanagerConfig(stgBucket),
          },
        },
      };
      break;

    case 'prod':
      config = {
        name: 'prod',
        accountId: '472057503814', // umccr_production
        stackProps: {
          orcaBusStatefulConfig: {
            schemaRegistryProps: {
              ...orcaBusStatefulConfig.schemaRegistryProps,
            },
            eventBusProps: {
              ...orcaBusStatefulConfig.eventBusProps,
            },
            databaseProps: {
              ...orcaBusStatefulConfig.databaseProps,
              numberOfInstance: 1,
              minACU: 0.5,
              maxACU: 16,
              removalPolicy: RemovalPolicy.RETAIN,
            },
            securityGroupProps: {
              ...orcaBusStatefulConfig.securityGroupProps,
            },
            eventSourceProps: eventSourceConfig(prodBucket),
          },
          orcaBusStatelessConfig: {
            ...orcaBusStatelessConfig,
            filemanagerConfig: filemanagerConfig(prodBucket),
          },
        },
      };
      break;
  }

  validateSecretName(config.stackProps.orcaBusStatefulConfig.databaseProps.masterSecretName);

  return config;
};
