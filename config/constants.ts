import { OrcaBusStatefulConfig } from '../lib/workload/orcabus-stateful-stack';
import { AuroraPostgresEngineVersion } from 'aws-cdk-lib/aws-rds';
import { OrcaBusStatelessConfig } from '../lib/workload/orcabus-stateless-stack';

const regName: string = 'OrcaBusSchemaRegistry';

export const orcaBusStatefulConfig: OrcaBusStatefulConfig = {
  schemaRegistryProps: {
    registryName: regName,
    description: 'Registry for OrcaBus Events',
  },
  eventBusProps: {
    eventBusName: 'OrcaBusMain',
    archiveName: 'OrcaBusMainArchive',
    archiveDescription: 'OrcaBus main event bus archive',
    archiveRetention: 365,
  },
  databaseProps: {
    clusterIdentifier: 'orcabus-db',
    defaultDatabaseName: 'orcabus',
    version: AuroraPostgresEngineVersion.VER_14_6,
    parameterGroupName: 'default.aurora-postgresql14',
    username: 'admin',
  },
  securityGroupProps: {
    securityGroupName: 'OrcaBusLambdaSecurityGroup',
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
        schemaLocation: __dirname + '/event_schemas/BclConvertWorkflowRequest.json',
      },
      {
        schemaName: 'DragenWgsQcWorkflowRequest',
        schemaDescription: 'Request event for DragenWgsQcWorkflowRequest',
        schemaLocation: __dirname + '/event_schemas/DragenWgsQcWorkflowRequest.json',
      },
    ],
  },
  bclConvertFunctionName: 'orcabus_bcl_convert',
};
