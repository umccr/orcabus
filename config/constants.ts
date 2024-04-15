import { AuroraPostgresEngineVersion } from 'aws-cdk-lib/aws-rds';
import { VpcLookupOptions } from 'aws-cdk-lib/aws-ec2';
import { Duration, RemovalPolicy } from 'aws-cdk-lib';
import { EventSourceProps } from '../lib/workload/stateful/stacks/shared/constructs/event-source';
import { DbAuthType } from '../lib/workload/stateless/stacks/postgres-manager/function/type';
import {
  FILEMANAGER_SERVICE_NAME,
  FilemanagerConfig,
} from '../lib/workload/stateless/stacks/filemanager/deploy/lib/filemanager';
import { IcaEventPipeStackProps } from '../lib/workload/stateful/stacks/ica-event-pipe/stack';
import { StatefulStackCollectionProps } from '../lib/workload/stateful/statefulStackCollectionClass';
import { StatelessStackCollectionProps } from '../lib/workload/stateless/statelessStackCollectionClass';
import { SequenceRunManagerStackProps } from '../lib/workload/stateless/stacks/sequence-run-manager/deploy/component';
import { MetadataManagerStackProps } from '../lib/workload/stateless/stacks/metadata-manager/deploy/stack';
import { PostgresManagerStackProps } from '../lib/workload/stateless/stacks/postgres-manager/deploy/stack';

const region = 'ap-southeast-2';

// upstream infra: vpc
const vpcName = 'main-vpc';
const vpcStackName = 'networking';
const vpcProps: VpcLookupOptions = {
  vpcName: vpcName,
  tags: {
    Stack: vpcStackName,
  },
};

// upstream infra: cognito
const cognitoUserPoolIdParameterName = '/data_portal/client/cog_user_pool_id';
const cognitoPortalAppClientIdParameterName = '/data_portal/client/data2/cog_app_client_id_stage';

const regName = 'OrcaBusSchemaRegistry';
const eventBusName = 'OrcaBusMain';
const computeSecurityGroupName = 'OrcaBusSharedComputeSecurityGroup';
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

const icaEventPipeProps: IcaEventPipeStackProps = {
  name: 'IcaEventPipeStack',
  eventBusName: eventBusName,
  slackTopicName: 'AwsChatBotTopic',
};

const serviceUserSecretName = 'orcabus/token-service-user'; // pragma: allowlist secret
const jwtSecretName = 'orcabus/token-service-jwt'; // pragma: allowlist secret

const statefulConfig = {
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
    secretRotationSchedule: Duration.days(7),
  },
  computeProps: {
    securityGroupName: computeSecurityGroupName,
  },
  icaEventPipeProps: icaEventPipeProps,
  tokenServiceProps: {
    serviceUserSecretName: serviceUserSecretName,
    jwtSecretName: jwtSecretName,
    vpcProps: vpcProps,
    cognitoUserPoolIdParameterName: cognitoUserPoolIdParameterName,
    cognitoPortalAppClientIdParameterName: cognitoPortalAppClientIdParameterName,
  },
};

const sequenceRunManagerStackProps: SequenceRunManagerStackProps = {
  vpcProps,
  lambdaSecurityGroupName: computeSecurityGroupName,
  mainBusName: eventBusName,
};

const metadataManagerStackProps: MetadataManagerStackProps = {
  vpcProps,
  lambdaSecurityGroupName: computeSecurityGroupName,
};

const postgresManagerStackProps: PostgresManagerStackProps = {
  vpcProps,
  lambdaSecurityGroupName: computeSecurityGroupName,
  masterSecretName: rdsMasterSecretName,
  dbClusterIdentifier: dbClusterIdentifier,
  clusterResourceIdParameterName: dbClusterResourceIdParameterName,
  dbPort: databasePort,
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
  secretRotationSchedule: Duration.days(7),
};

// const statelessConfig = {
//   multiSchemaConstructProps: {
//     registryName: regName,
//     schemas: [
//       {
//         schemaName: 'BclConvertWorkflowRequest',
//         schemaDescription: 'Request event for BclConvertWorkflow',
//         schemaType: 'OpenApi3',
//         schemaLocation: __dirname + '/event_schemas/BclConvertWorkflowRequest.json',
//       },
//       {
//         schemaName: 'DragenWgsQcWorkflowRequest',
//         schemaDescription: 'Request event for DragenWgsQcWorkflowRequest',
//         schemaType: 'OpenApi3',
//         schemaLocation: __dirname + '/event_schemas/DragenWgsQcWorkflowRequest.json',
//       },
//     ],
//   },
//   eventBusName: eventBusName,
//   computeSecurityGroupName: computeSecurityGroupName,
//   rdsMasterSecretName: rdsMasterSecretName,
// };

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
    securityGroupName: computeSecurityGroupName,
    vpcProps,
    eventSourceQueueName: eventSourceQueueName,
    databaseClusterEndpointHostParameter:
      statefulConfig.databaseProps.clusterEndpointHostParameterName,
    port: databasePort,
    eventSourceBuckets: [bucket],
  };
};

interface EnvironmentConfig {
  name: string;
  region: string;
  accountId: string;
  stackProps: {
    statefulConfig: StatefulStackCollectionProps;
    statelessConfig: StatelessStackCollectionProps;
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
        region,
        accountId: '843407916570', // umccr_development
        stackProps: {
          statefulConfig: {
            sharedStackProps: {
              vpcProps,
              schemaRegistryProps: statefulConfig.schemaRegistryProps,
              eventBusProps: statefulConfig.eventBusProps,
              databaseProps: {
                ...statefulConfig.databaseProps,
                numberOfInstance: 1,
                minACU: 0.5,
                maxACU: 16,
                enhancedMonitoringInterval: Duration.seconds(60),
                enablePerformanceInsights: true,
                removalPolicy: RemovalPolicy.DESTROY,
              },
              computeProps: statefulConfig.computeProps,
              eventSourceProps: eventSourceConfig(devBucket),
            },
            tokenServiceStackProps: statefulConfig.tokenServiceProps,
            icaEventPipeStackProps: statefulConfig.icaEventPipeProps,
          },
          statelessConfig: {
            postgresManagerStackProps: postgresManagerStackProps,
            metadataManagerStackProps: metadataManagerStackProps,
            sequenceRunManagerStackProps: sequenceRunManagerStackProps,
            fileManagerStackProps: filemanagerConfig(devBucket),
          },
        },
      };
      break;

    case 'gamma':
      config = {
        name: 'gamma',
        region,
        accountId: '455634345446', // umccr_staging
        stackProps: {
          statefulConfig: {
            sharedStackProps: {
              vpcProps,
              schemaRegistryProps: statefulConfig.schemaRegistryProps,
              eventBusProps: statefulConfig.eventBusProps,
              databaseProps: {
                ...statefulConfig.databaseProps,
                numberOfInstance: 1,
                minACU: 0.5,
                maxACU: 16,
                enhancedMonitoringInterval: Duration.seconds(60),
                enablePerformanceInsights: true,
                removalPolicy: RemovalPolicy.DESTROY,
              },
              computeProps: statefulConfig.computeProps,
              eventSourceProps: eventSourceConfig(stgBucket),
            },
            tokenServiceStackProps: statefulConfig.tokenServiceProps,
            icaEventPipeStackProps: statefulConfig.icaEventPipeProps,
          },
          statelessConfig: {
            postgresManagerStackProps: postgresManagerStackProps,
            metadataManagerStackProps: metadataManagerStackProps,
            sequenceRunManagerStackProps: sequenceRunManagerStackProps,
            fileManagerStackProps: filemanagerConfig(stgBucket),
          },
        },
      };
      break;

    case 'prod':
      config = {
        name: 'prod',
        region,
        accountId: '472057503814', // umccr_production
        stackProps: {
          statefulConfig: {
            sharedStackProps: {
              vpcProps,
              schemaRegistryProps: statefulConfig.schemaRegistryProps,
              eventBusProps: statefulConfig.eventBusProps,
              databaseProps: {
                ...statefulConfig.databaseProps,
                numberOfInstance: 1,
                minACU: 0.5,
                maxACU: 16,
                removalPolicy: RemovalPolicy.RETAIN,
              },
              computeProps: statefulConfig.computeProps,
              eventSourceProps: eventSourceConfig(prodBucket),
            },
            tokenServiceStackProps: statefulConfig.tokenServiceProps,
            icaEventPipeStackProps: statefulConfig.icaEventPipeProps,
          },
          statelessConfig: {
            postgresManagerStackProps: postgresManagerStackProps,
            metadataManagerStackProps: metadataManagerStackProps,
            sequenceRunManagerStackProps: sequenceRunManagerStackProps,
            fileManagerStackProps: filemanagerConfig(prodBucket),
          },
        },
      };
      break;
  }

  // validateSecretName(config.stackProps.statefulConfig.databaseProps.masterSecretName);

  return config;
};
