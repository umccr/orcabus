import { Client } from 'pg';
import {
  EventType,
  getMicroserviceConfig,
  getMicroserviceName,
  executeSqlWithLog,
  getRdsMasterSecret,
} from './utils';

export const handler = async (event: EventType) => {
  const microserviceConfig = getMicroserviceConfig();
  const microserviceName = getMicroserviceName(microserviceConfig, event);
  const pgMasterConfig = await getRdsMasterSecret();

  const pgClient = new Client(pgMasterConfig);
  await pgClient.connect();
  console.info('connected to RDS with master credential');

  // create microservice db
  console.info('create a new database for the given microservice microserviceName');
  const createDbQuery = `CREATE DATABASE ${microserviceName};`;
  await executeSqlWithLog(pgClient, createDbQuery);

  // restrict privileged access
  console.info('restrict database access from public');
  const restrictPrivilegedQuery = `REVOKE ALL ON DATABASE ${microserviceName} FROM PUBLIC;`;
  await executeSqlWithLog(pgClient, restrictPrivilegedQuery);

  await pgClient.end();
};
