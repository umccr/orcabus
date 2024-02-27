import { generate as pass_generator } from 'generate-password';
import {
  executeSqlWithLog,
  getMicroserviceName,
  getMicroserviceConfig,
  getRdsMasterSecret,
  DbAuthType,
} from './utils';
import {
  SecretsManagerClient,
  CreateSecretCommandInput,
  CreateSecretCommand,
} from '@aws-sdk/client-secrets-manager';
import { Client } from 'pg';

type EventType = {
  microserviceName: string;
};

export const handler = async (event: EventType) => {
  const microserviceConfig = getMicroserviceConfig();
  const microserviceName = getMicroserviceName(microserviceConfig, event);
  const pgMasterConfig = await getRdsMasterSecret();

  const findConfig = microserviceConfig.find((e) => e.name == microserviceName);
  if (findConfig?.authType != DbAuthType.USERNAME_PASSWORD) {
    throw new Error('this microservice is not configured for username-password authentication');
  }

  const client = new Client(pgMasterConfig);
  await client.connect();
  console.info('connected to RDS with master credential');

  // create a new role
  console.info('creating a user-password login role');
  const password = pass_generator({ length: 10, numbers: true });
  const createRoleQueryTemplate = `CREATE ROLE ${microserviceName} with LOGIN ENCRYPTED PASSWORD '${password}'`;
  await executeSqlWithLog(client, createRoleQueryTemplate);

  await client.end();

  // store the new db config at secret manager
  const secretValue = createSecretValue({
    password: password,
    host: pgMasterConfig.host,
    port: pgMasterConfig.port,
    username: microserviceName,
    dbname: microserviceName,
  });

  const smClient = new SecretsManagerClient();
  const smInput: CreateSecretCommandInput = {
    Name: `orcabus/microservice/${microserviceName}`,
    Description: `orcabus microservice secret for '${microserviceName}'`,
    SecretString: JSON.stringify(secretValue),
    Tags: [
      { Key: 'stack', Value: 'manual' },
      { Key: 'useCase', Value: 'store credential for the orcabus microservice' },
      { Key: 'creator', Value: 'postgres_microservice at the orcabus stateless stack' },
    ],
  };
  const smCommand = new CreateSecretCommand(smInput);

  console.info(
    `storing the role credential at the secret manager (orcabus/microservice/${microserviceName})`
  );
  const response = await smClient.send(smCommand);
  console.info(`ssm-response: ${response}`);
};

/**
 * create secret manager value for postgres format
 */
const createSecretValue = (props: {
  host: string;
  username: string;
  password: string;
  dbname: string;
  port: string;
}) => {
  return {
    engine: 'postgres',
    host: props.host,
    username: props.username,
    password: props.password,
    dbname: props.dbname,
    port: props.port,
  };
};
