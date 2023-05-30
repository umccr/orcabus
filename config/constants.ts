import { OrcaBusStatefulConfig } from '../lib/workload/orcabus-stateful-stack';
import { AuroraMysqlEngineVersion } from 'aws-cdk-lib/aws-rds';
import { OrcaBusStatelessConfig } from '../lib/workload/orcabus-stateless-stack';
import { aws_lambda } from 'aws-cdk-lib';

const regName = 'OrcaBusSchemaRegistry';
const eventBusName = 'OrcaBusMain';
const lambdaSecurityGroupName = 'OrcaBusLambdaSecurityGroup';

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
    version: AuroraMysqlEngineVersion.VER_3_02_2,
    parameterGroupName: 'default.aurora-mysql8.0',
    username: 'admin',
  },
  securityGroupProps: {
    securityGroupName: lambdaSecurityGroupName,
    securityGroupDescription: 'Allow within same SecurityGroup',
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
        accountId: '843407916570',
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
              maxACU: 1,
            },
            securityGroupProps: {
              ...orcaBusStatefulConfig.securityGroupProps,
            },
          },
          orcaBusStatelessConfig: orcaBusStatelessConfig,
        },
      };

    case 'gamma':
      return {
        name: 'gamma',
        // TODO: Change this Account Number
        accountId: '1234567',
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
              maxACU: 1,
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
        // TODO: Change this account number
        accountId: '123456789',
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
              minACU: 2,
              maxACU: 4,
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
