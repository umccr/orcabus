import axios from 'axios';
import { Client } from 'pg';

/**
 * There are 2 ways of connecting from microservice to db
 */
export enum DbAuthType {
  RDS_IAM,
  USERNAME_PASSWORD,
}

export type EventType = {
  microserviceName: string;
};

export type MicroserviceConfig = {
  name: string;
  authType: DbAuthType;
}[];

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

  const rdsSecret = JSON.parse(await getSecretManagerWithLayerExtension(rdsSecretName));

  return {
    host: rdsSecret.host,
    port: rdsSecret.port,
    database: rdsSecret.dbname,
    user: rdsSecret.username,
    password: rdsSecret.password,
  };
};

/**
 * Wrapper to use the default lambda layer extension to query secret manager
 * Ref: https://docs.aws.amazon.com/secretsmanager/latest/userguide/retrieving-secrets_lambda.html
 * @param secretManagerName The microserviceName of the secret or ARN
 * @returns
 */
export const getSecretManagerWithLayerExtension = async (secretManagerName: string) => {
  const apiUrl = `http://localhost:2773/secretsmanager/get?secretId=${encodeURIComponent(
    secretManagerName
  )}`;
  const headers = { 'X-Aws-Parameters-Secrets-Token': process.env.AWS_SESSION_TOKEN };
  const res = await axios.get(apiUrl, {
    headers: headers,
  });

  return res.data.SecretString;
};
