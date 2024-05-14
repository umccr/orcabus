import { Client } from 'pg';

export const listDatabase = async (client: Client): Promise<string[]> => {
  console.info('list existing database');
  const query = `SELECT datname FROM pg_database WHERE datistemplate = false;`;

  console.info('QUERY: ', query);
  const res = await client.query(query);
  console.info('RESPONSE: ', JSON.stringify(res.rows, undefined, 2));

  return res.rows.map((element) => element.datname);
};

export const listRole = async (client: Client): Promise<string[]> => {
  console.info('list existing role');
  const query = `SELECT usename FROM pg_user;`;

  console.info('QUERY: ', query);
  const res = await client.query(query);
  console.info('RESPONSE: ', JSON.stringify(res.rows, undefined, 2));

  return res.rows.map((element) => element.usename);
};

export const createDatabase = async (client: Client, databaseName: string, owner: string) => {
  console.info(`creating a new database for the given microservice: ${databaseName}`);
  const createDbQuery = `CREATE DATABASE ${databaseName};`;
  console.info('QUERY: ', createDbQuery);
  await client.query(createDbQuery);

  console.info(`restricting database access from public ${databaseName}`);
  const restrictPrivilegedQuery = `REVOKE ALL ON DATABASE ${databaseName} FROM PUBLIC;`;
  console.info('QUERY: ', restrictPrivilegedQuery);
  await client.query(restrictPrivilegedQuery);

  console.info(`alter database to its owner: ${owner}`);
  const alterDbRole = `ALTER DATABASE ${databaseName} OWNER TO ${owner}`;
  console.info('QUERY: ', alterDbRole);
  await client.query(alterDbRole);
};

export const createUserPassLoginRole = async (
  client: Client,
  roleName: string,
  password: string
) => {
  console.info(`creating a new user-pass login role: ${roleName}`);
  const query = `CREATE ROLE ${roleName} with LOGIN ENCRYPTED PASSWORD '${password}'`;
  console.info('QUERY: ', `CREATE ROLE ${roleName} with LOGIN ENCRYPTED PASSWORD '***'`);
  await client.query(query);
};

export const createRdsIamLoginRole = async (client: Client, roleName: string) => {
  console.info(`creating a new rds_iam login role: ${roleName}`);
  const query = `CREATE USER ${roleName}; GRANT rds_iam TO ${roleName};`;

  console.info('QUERY: ', query);
  await client.query(query);
};

export const listRdsIamRole = async (client: Client): Promise<string[]> => {
  console.info('list existing rds_iam role');
  const query =
    'SELECT r.rolname ' +
    'FROM pg_roles r ' +
    'JOIN pg_auth_members m ON r.oid = m.member ' +
    'JOIN pg_roles rr ON m.roleid = rr.oid ' +
    `WHERE rr.rolname = 'rds_iam';`;

  console.info('QUERY: ', query);

  const res = await client.query(query);
  console.info('RESPONSE: ', JSON.stringify(res.rows, undefined, 2));

  return res.rows.map((element) => element.rolname);
};

export const grantRdsIamRole = async (client: Client, roleName: string) => {
  console.info(`granting rds_iam role to user: ${roleName}`);
  const query = `GRANT rds_iam TO ${roleName};`;

  console.info('QUERY: ', query);
  await client.query(query);
};
export const revokeRdsIamRole = async (client: Client, roleName: string) => {
  console.info(`revoking rds_iam role from user: ${roleName}`);
  const query = `REVOKE rds_iam FROM ${roleName};`;

  console.info('QUERY: ', query);
  await client.query(query);
};

export const alterPassRole = async (client: Client, roleName: string, password: string) => {
  console.info(`alter role password: ${roleName}`);
  const query = `ALTER ROLE ${roleName} WITH LOGIN ENCRYPTED PASSWORD '${password}'`;
  console.info('QUERY: ', `ALTER ROLE ${roleName} WITH LOGIN ENCRYPTED PASSWORD '***'`);
  await client.query(query);
};
