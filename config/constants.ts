import { OrcaBusStatefulConfig } from '../lib/workload/orcabus-stateful-stack';
import { AuroraPostgresEngineVersion } from 'aws-cdk-lib/aws-rds';
import {
  FilemanagerDependencies,
  OrcaBusStatelessConfig,
} from '../lib/workload/orcabus-stateless-stack';
import { Duration, aws_lambda, RemovalPolicy } from 'aws-cdk-lib';
import { EventSourceProps } from '../lib/workload/stateful/event_source/component';

const regName = 'OrcaBusSchemaRegistry';
const eventBusName = 'OrcaBusMain';
const lambdaSecurityGroupName = 'OrcaBusLambdaSecurityGroup';
const rdsMasterSecretName = 'orcabus/rds-master'; // pragma: allowlist secret

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
    clusterIdentifier: 'orcabus-db',
    defaultDatabaseName: 'orcabus',
    version: AuroraPostgresEngineVersion.VER_15_4,
    parameterGroupName: 'default.aurora-postgresql15',
    username: 'postgres',
    dbPort: 5432,
    masterSecretName: rdsMasterSecretName,
    securityGroupName: 'orcabus-database-security-group',
    monitoring: {
      cloudwatchLogsExports: ['orcabus-postgresql'],
    },
    inboundSecurityGroupName: 'inbound-database-security-group',
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
  lambdaRuntimePythonVersion: aws_lambda.Runtime.PYTHON_3_10,
  bclConvertFunctionName: 'orcabus_bcl_convert',
  rdsMasterSecretName: rdsMasterSecretName,
};

const eventSourceConfig: EventSourceProps = {
  queueName: 'orcabus-event-source-queue',
  maxReceiveCount: 3,
  rules: [
    {
      bucket: 'umccr-temp-dev',
    },
  ],
};

const filemanagerDependencies: FilemanagerDependencies = {
  eventSourceBuckets: ['umccr-temp-dev'],
  eventSourceQueueName: eventSourceConfig.queueName,
  databaseSecretName: orcaBusStatefulConfig.databaseProps.masterSecretName,
  databaseSecurityGroupName: orcaBusStatefulConfig.databaseProps.inboundSecurityGroupName,
};

interface EnvironmentConfig {
  name: string;
  accountId: string;
  stackProps: {
    orcaBusStatefulConfig: OrcaBusStatefulConfig;
    orcaBusStatelessConfig: OrcaBusStatelessConfig;
  };
}
export const getEnvironmentConfig = (
  accountName: 'beta' | 'gamma' | 'prod'
): EnvironmentConfig | null => {
  switch (accountName) {
    case 'beta':
      return {
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
            eventSourceProps: eventSourceConfig,
          },
          orcaBusStatelessConfig: {
            ...orcaBusStatelessConfig,
            filemanagerDependencies: filemanagerDependencies,
          },
        },
      };

    case 'gamma':
      return {
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
          },
          orcaBusStatelessConfig: orcaBusStatelessConfig,
        },
      };

    case 'prod':
      return {
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
          },
          orcaBusStatelessConfig: orcaBusStatelessConfig,
        },
      };

    default:
      return null;
  }
};
