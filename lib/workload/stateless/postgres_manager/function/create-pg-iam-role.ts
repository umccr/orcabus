import { Client } from 'pg';
import {
  EventType,
  getMicroserviceConfig,
  getMicroserviceName,
  executeSqlWithLog,
  getRdsMasterSecret,
  DbAuthType,
} from './utils';

export const handler = async (event: EventType) => {
  const microserviceConfig = getMicroserviceConfig();
  const microserviceName = getMicroserviceName(microserviceConfig, event);
  const pgMasterConfig = await getRdsMasterSecret();

  const findConfig = microserviceConfig.find((e) => e.name == microserviceName);
  if (findConfig?.authType != DbAuthType.RDS_IAM) {
    throw new Error('this microservice is not configured for rds_iam');
  }

  const pgClient = new Client(pgMasterConfig);
  await pgClient.connect();
  console.info('connected to RDS with master credential');

  // create a new role
  console.info('create new user that has the rds_iam role');
  const assignRdsIamQuery = `CREATE USER ${microserviceName}; GRANT rds_iam TO ${microserviceName};`;
  await executeSqlWithLog(pgClient, assignRdsIamQuery);

  await pgClient.end();
};
