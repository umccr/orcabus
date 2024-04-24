import { Client } from 'pg';
import { listDatabase, listRdsIamRole, listRole } from '../function/psql-commands';
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

describe('test update Db and Role handler', () => {
  beforeAll(async () => {
    process.env.MICRO_SECRET_MANAGER_TEMPLATE_NAME =
      'orcabus/{replace_microservice_name}/rds-login-credential';

    const pgClient = new Client(LOCAL_DB_CONFIG);
    await pgClient.connect();

    const createRdsIamRole = `
    DO $$
      BEGIN
        IF NOT EXISTS (
            SELECT FROM pg_roles WHERE rolname = 'rds_iam'
        ) 
        THEN
            CREATE USER rds_iam;
        END IF;
      END
      $$;
    `;
    await pgClient.query(createRdsIamRole);

    await pgClient.end();
  });

  test(`test on new role and Db`, async () => {
    process.env.MICROSERVICE_CONFIG = JSON.stringify([
      { name: 'app_user_pass', authType: DbAuthType.USERNAME_PASSWORD },
      { name: 'app_rds_iam', authType: DbAuthType.RDS_IAM },
    ]);
    const pgClient = new Client(LOCAL_DB_CONFIG);
    await pgClient.connect();

    await updatePgDbAndRole();

    const db = await listDatabase(pgClient);
    const user = await listRole(pgClient);
    const rdsIamRole = await listRdsIamRole(pgClient);

    // check all databases created
    expect(db.includes('app_user_pass')).toBeTruthy();
    expect(db.includes('app_rds_iam')).toBeTruthy();

    // check all roles created
    expect(user.includes('app_user_pass')).toBeTruthy();
    expect(user.includes('app_rds_iam')).toBeTruthy();

    // check if user is created as rds_iam role
    expect(rdsIamRole.includes('app_rds_iam')).toBeTruthy();
    expect(rdsIamRole.includes('app_user_pass')).toBeFalsy();

    await pgClient.end();
  });

  test(`test on alter role authType`, async () => {
    process.env.MICROSERVICE_CONFIG = JSON.stringify([
      { name: 'app_1', authType: DbAuthType.USERNAME_PASSWORD },
      { name: 'app_2', authType: DbAuthType.RDS_IAM },
    ]);
    const pgClient = new Client(LOCAL_DB_CONFIG);
    await pgClient.connect();

    await updatePgDbAndRole();

    const user = await listRole(pgClient);
    const rdsIamRole = await listRdsIamRole(pgClient);

    // check all roles created
    expect(user.includes('app_1')).toBeTruthy();
    expect(user.includes('app_2')).toBeTruthy();

    // check if user is created as rds_iam role
    expect(rdsIamRole.includes('app_1')).toBeFalsy();
    expect(rdsIamRole.includes('app_2')).toBeTruthy();

    process.env.MICROSERVICE_CONFIG = JSON.stringify([
      { name: 'app_1', authType: DbAuthType.RDS_IAM },
      { name: 'app_2', authType: DbAuthType.USERNAME_PASSWORD },
    ]);

    await updatePgDbAndRole();

    const new_user = await listRole(pgClient);
    const new_rdsIamRole = await listRdsIamRole(pgClient);

    // check all roles created
    expect(new_user.includes('app_1')).toBeTruthy();
    expect(new_user.includes('app_2')).toBeTruthy();

    // check if user is created as rds_iam role
    expect(new_rdsIamRole.includes('app_1')).toBeTruthy();
    expect(new_rdsIamRole.includes('app_2')).toBeFalsy();

    await pgClient.end();
  });
});
