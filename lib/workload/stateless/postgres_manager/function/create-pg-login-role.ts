import { DbAuthType } from './type';
import {
  getMicroserviceName,
  getMicroserviceConfig,
  getRdsMasterSecret,
  getSecretValue,
} from './utils';
import { SecretsManagerClient } from '@aws-sdk/client-secrets-manager';
import { Client } from 'pg';

type EventType = {
  microserviceName: string;
};

export const handler = async (event: EventType) => {
  const smClient = new SecretsManagerClient();
  const microserviceConfig = getMicroserviceConfig();
  const microserviceName = getMicroserviceName(microserviceConfig, event);
  const pgMasterConfig = await getRdsMasterSecret();

  // validate if db is configured for username-password auth
  const findConfig = microserviceConfig.find((e) => e.name == microserviceName);
  if (findConfig?.authType != DbAuthType.USERNAME_PASSWORD) {
    throw new Error('this microservice is not configured for username-password authentication');
  }

  // get db config for
  const pgClient = new Client(pgMasterConfig);
  await pgClient.connect();
  console.info('connected to RDS with master credential');

  // create a new role
  console.info('creating a user-password login role');

  // get microservice app password from the secret-manager
  const microserviceSecretName = process.env.MICRO_SECRET_MANAGER_TEMPLATE_NAME?.replace(
    '{replace_microservice_name}',
    microserviceName
  );
  if (!microserviceSecretName)
    throw new Error('No microservice secret name configure in the env variable');

  const SMValue = JSON.parse(await getSecretValue(microserviceSecretName));
  const SMPassword = SMValue?.password;
  if (!SMPassword) throw new Error('No password output from password generator');

  // run the create role
  const createRolePasswordSQL = `CREATE ROLE ${microserviceName} with LOGIN ENCRYPTED PASSWORD '${SMPassword}'`;
  console.info(
    `RESULT: ${JSON.stringify(await pgClient.query(createRolePasswordSQL), undefined, 2)}`
  );

  await pgClient.end();
};
