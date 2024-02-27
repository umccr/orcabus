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

  const client = new Client(pgMasterConfig);
  await client.connect();
  console.info('connected to RDS with master credential');

  // assign db to this role to their own db
  console.info('alter database to be owned by this new role');
  const alterDbRoleQuery = `ALTER DATABASE ${microserviceName} OWNER TO ${microserviceName}`;
  await executeSqlWithLog(client, alterDbRoleQuery);

  await client.end();
};
