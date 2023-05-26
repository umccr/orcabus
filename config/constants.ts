import { OrcaBusStatefulConfig } from '../lib/workload/orcabus-stateful-stack';
import { AuroraMysqlEngineVersion } from 'aws-cdk-lib/aws-rds';
import { OrcaBusStatelessConfig } from '../lib/workload/orcabus-stateless-stack';
import { aws_lambda } from 'aws-cdk-lib';

const regName = 'OrcaBusSchemaRegistry';
const eventBusName = 'OrcaBusMain';
const lambdaSecurityGroupName = 'OrcaBusLambdaSecurityGroup';

export const orcaBusStatefulConfig: OrcaBusStatefulConfig = {
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

export const orcaBusStatelessConfig: OrcaBusStatelessConfig = {
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
}
export const getEnvironmentConfig = (
  accountName: 'beta' | 'gamma' | 'prod'
): EnvironmentConfig | null => {
  switch (accountName) {
    case 'beta':
      return {
        name: 'beta',
        accountId: '843407916570',
      };

    default:
      return null;
  }
};
