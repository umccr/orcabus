import { Client } from 'pg';
import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';
import { MicroserviceConfig } from './type';

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

export const getMicroservicePassword = async (microserviceName: string): Promise<string> => {
  const microserviceSecretName = process.env.MICRO_SECRET_MANAGER_TEMPLATE_NAME?.replace(
    '{replace_microservice_name}',
    microserviceName
  );
  if (!microserviceSecretName)
    throw new Error(`No microservice secret name configure in the env variable`);

  const SMValue = JSON.parse(await getSecretValue(microserviceSecretName));
  const SMPassword = SMValue?.password;
  if (!SMPassword) throw new Error('No password output from password generator');

  return SMPassword;
};
