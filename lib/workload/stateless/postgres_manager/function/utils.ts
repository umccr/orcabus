import { Client } from 'pg';
import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';
import { MicroserviceConfig, EventType } from './type';

/**
 * get microservice config from lambda environment
 * @returns
 */
export const getMicroserviceConfig = (): MicroserviceConfig => {
  if (!process.env.MICROSERVICE_CONFIG) {
    throw new Error('no microservice is configured in this lambda');
  }
  const microserviceConfig = JSON.parse(process.env.MICROSERVICE_CONFIG) as MicroserviceConfig;
  return microserviceConfig;
};

/**
 * get microservice name from the event payload and validate with the configuration
 * @param event
 * @returns
 */
export const getMicroserviceName = (
  microserviceConfig: MicroserviceConfig,
  event: EventType
): string => {
  const eventName = event.microserviceName;
  if (!eventName) {
    throw new Error('Microservice microserviceName is not defined in the event payload');
  }

  const configNameArray = microserviceConfig.map((v) => v.name);
  if (!configNameArray.includes(eventName)) {
    throw new Error('invalid event microservice name');
  }

  return eventName;
};

/**
 * Execute postgres sql statement with some logs
 * @param client
 * @param sqlStatement
 */
export const executeSqlWithLog = async (client: Client, sqlStatement: string) => {
  console.info(`QUERY: ${sqlStatement}`);
  console.info(`RESULT: ${JSON.stringify(await client.query(sqlStatement), undefined, 2)}`);
};

/**
 * get the rds master secret from secret manager and return in pg.Client config format
 * @returns
 */
export const getRdsMasterSecret = async () => {
  const rdsSecretName = process.env.RDS_SECRET_MANAGER_NAME;
  if (!rdsSecretName) throw new Error('No RDS master secret configure in the env variable');

  const rdsSecret = JSON.parse(await getSecretValue(rdsSecretName));

  return {
    host: rdsSecret.host,
    port: rdsSecret.port,
    database: rdsSecret.dbname,
    user: rdsSecret.username,
    password: rdsSecret.password,
  };
};

export const getSecretValue = async (secretManagerName: string) => {
  const client = new SecretsManagerClient();
  const response = await client.send(
    new GetSecretValueCommand({
      SecretId: secretManagerName,
    })
  );

  if (response.SecretString) {
    return response.SecretString;
  }

  throw new Error('Failed to retrieve secret value');
};
