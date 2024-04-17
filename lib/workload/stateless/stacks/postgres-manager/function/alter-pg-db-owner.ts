import { Client } from 'pg';
import {
  getMicroserviceConfig,
  getMicroserviceName,
  executeSqlWithLog,
  getRdsMasterSecret,
} from './utils';
import { EventType } from './type';

export const handler = async (event: EventType) => {
  const microserviceConfig = getMicroserviceConfig();
  const microserviceName = getMicroserviceName(microserviceConfig, event);
  const pgMasterConfig = await getRdsMasterSecret();

  const pgClient = new Client(pgMasterConfig);
  await pgClient.connect();
  console.info('connected to RDS with master credential');

  // assign db to this role to their own db
  console.info('alter database to be owned by this new role');
  const alterDbRoleQuery = `ALTER DATABASE ${microserviceName} OWNER TO ${microserviceName}`;
  await executeSqlWithLog(pgClient, alterDbRoleQuery);

  await pgClient.end();
};
