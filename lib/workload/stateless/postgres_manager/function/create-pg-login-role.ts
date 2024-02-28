import {
  getMicroserviceName,
  getMicroserviceConfig,
  getRdsMasterSecret,
  DbAuthType,
} from './utils';
import {
  SecretsManagerClient,
  CreateSecretCommandInput,
  CreateSecretCommand,
  GetRandomPasswordCommandInput,
  GetRandomPasswordCommand,
} from '@aws-sdk/client-secrets-manager';
import { Client } from 'pg';

type EventType = {
  microserviceName: string;
};

export const handler = async (event: EventType) => {
  const smClient = new SecretsManagerClient();
  const microserviceConfig = getMicroserviceConfig();
  const microserviceName = getMicroserviceName(microserviceConfig, event);
  const pgMasterConfig = await getRdsMasterSecret();

  const findConfig = microserviceConfig.find((e) => e.name == microserviceName);
  if (findConfig?.authType != DbAuthType.USERNAME_PASSWORD) {
    throw new Error('this microservice is not configured for username-password authentication');
  }

  const pgClient = new Client(pgMasterConfig);
  await pgClient.connect();
  console.info('connected to RDS with master credential');

  // create a new role
  console.info('creating a user-password login role');

  // get random password using aws secret manager sdk
  const randomPassConfig: GetRandomPasswordCommandInput = {
    PasswordLength: 32,
    ExcludePunctuation: true,
    RequireEachIncludedType: true,
  };
  const randomPassCommandInput = new GetRandomPasswordCommand(randomPassConfig);
  const randomPassResponse = await smClient.send(randomPassCommandInput);
  const password = randomPassResponse.RandomPassword;
  if (!password) throw new Error('No password output from password generator');

  // run the create role
  const createRolePasswordSQL = `CREATE ROLE ${microserviceName} with LOGIN ENCRYPTED PASSWORD '${password}'`;
  console.info(
    `RESULT: ${JSON.stringify(await pgClient.query(createRolePasswordSQL), undefined, 2)}`
  );

  await pgClient.end();

  // store the new db config at secret manager
  const secretValue = createSecretValue({
    password: password,
    host: pgMasterConfig.host,
    port: pgMasterConfig.port,
    username: microserviceName,
    dbname: microserviceName,
  });

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
  console.info(`ssm-response: ${JSON.stringify(response, undefined, 2)}`);
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
