import { Client } from 'pg';
import { getMicroservicePassword } from './utils';
import { getMicroserviceConfig, getRdsMasterSecret } from './utils';
import { DbAuthType } from './type';
import {
  createDatabase,
  createRdsIamLoginRole,
  createUserPassLoginRole,
  listDatabase,
  listRole,
} from './psql-commands';
import { CdkCustomResourceEvent, CdkCustomResourceResponse, Context } from 'aws-lambda';

export const handler = async (
  event: CdkCustomResourceEvent,
  context: Context
): Promise<CdkCustomResourceResponse> => {
  console.info('event: ', event);

  const resp: CdkCustomResourceResponse = {
    StackId: event.StackId,
    RequestId: event.RequestId,
    LogicalResourceId: event.LogicalResourceId,
    PhysicalResourceId: context.logGroupName,
  };

  if (event.RequestType == 'Delete') {
    return {
      ...resp,
      Status: 'SUCCESS',
    };
  }

  try {
    const result = await updatePgDbAndRole();

    return {
      ...resp,
      Status: 'SUCCESS',
      Data: result,
    };
  } catch (error) {
    console.error(error);

    if (error instanceof Error) {
      resp.Reason = error.message;
    }
    return {
      ...resp,
      Status: 'FAILED',
      Data: { Result: error },
    };
  }
};

export const updatePgDbAndRole = async () => {
  const result: Record<string, string[]> = {
    existingRoles: [],
    existingDatabases: [],
    newIamRole: [],
    newUserPassRole: [],
    newDatabase: [],
  };

  const microserviceConfig = getMicroserviceConfig();
  const pgMasterConfig = await getRdsMasterSecret();

  const pgClient = new Client(pgMasterConfig);
  await pgClient.connect();

  const roleList = await listRole(pgClient);
  const dbList = await listDatabase(pgClient);

  result.existingRoles.concat(roleList);
  result.existingDatabases.concat(dbList);

  // iterate for each microservice name configured
  for (const m of microserviceConfig) {
    // upsert role from the configuration file
    if (!roleList.includes(m.name)) {
      // create role based on the auth type
      if (m.authType == DbAuthType.USERNAME_PASSWORD) {
        const pass = await getMicroservicePassword(m.name);
        await createUserPassLoginRole(pgClient, m.name, pass);

        result.newUserPassRole.push(m.name);
      } else if (m.authType == DbAuthType.RDS_IAM) {
        await createRdsIamLoginRole(pgClient, m.name);

        result.newIamRole.push(m.name);
      }
    }

    // upsert database from the configuration environment
    if (!dbList.includes(m.name)) {
      await createDatabase(pgClient, m.name, m.name);

      result.newDatabase.push(m.name);
    }
  }

  await pgClient.end();

  return result;
};
