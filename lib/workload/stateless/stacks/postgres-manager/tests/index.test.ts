import { Client } from 'pg';
import { listDatabase, listRole } from '../function/psql-commands';
import { updatePgDbAndRole } from '../function';
import { DbAuthType } from '../function/type';

const LOCAL_DB_CONFIG = {
  host: 'localhost',
  port: 5432,
  database: 'orcabus',
  user: 'orcabus',
  password: 'orcabus', // pragma: allowlist secret
};

jest.mock('../function/utils', () => {
  return {
    ...jest.requireActual('../function/utils'),
    getRdsMasterSecret: jest.fn().mockImplementation(() => {
      return LOCAL_DB_CONFIG;
    }),
    getMicroservicePassword: jest.fn().mockImplementation(() => {
      return '123';
    }),
  };
});

describe('test psql handler', () => {
  test(`test handler creation`, async () => {
    process.env.MICROSERVICE_CONFIG = JSON.stringify([
      { name: 'app_1', authType: DbAuthType.USERNAME_PASSWORD },
    ]);
    process.env.MICRO_SECRET_MANAGER_TEMPLATE_NAME =
      'orcabus/{replace_microservice_name}/rds-login-credential';

    await updatePgDbAndRole();

    const pgClient = new Client(LOCAL_DB_CONFIG);
    await pgClient.connect();
    const db = await listDatabase(pgClient);
    const user = await listRole(pgClient);

    expect(db.includes('app_1')).toBeTruthy();
    expect(user.includes('app_1')).toBeTruthy();

    pgClient.end();
  });
});
