import { Duration } from 'aws-cdk-lib';
import { FILEMANAGER_SERVICE_NAME } from '../../lib/workload/stateless/stacks/filemanager/deploy/stack';
import { PostgresManagerStackProps } from '../../lib/workload/stateful/stacks/postgres-manager/deploy/stack';
import { DbAuthType } from '../../lib/workload/stateful/stacks/postgres-manager/function/type';
import {
  computeSecurityGroupName,
  databasePort,
  dbClusterIdentifier,
  dbClusterResourceIdParameterName,
  rdsMasterSecretName,
  vpcProps,
} from '../constants';

export const getPostgresManagerStackProps = (): PostgresManagerStackProps => {
  return {
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
        name: 'workflow_manager',
        authType: DbAuthType.USERNAME_PASSWORD,
      },
      {
        name: 'metadata_manager',
        authType: DbAuthType.RDS_IAM,
      },
      { name: FILEMANAGER_SERVICE_NAME, authType: DbAuthType.RDS_IAM },
    ],
    secretRotationSchedule: Duration.days(7),
  };
};
