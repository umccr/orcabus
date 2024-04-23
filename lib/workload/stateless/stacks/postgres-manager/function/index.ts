import { Client } from 'pg';
import { getMicroservicePassword } from './utils';
import { getMicroserviceConfig, getRdsMasterSecret } from './utils';
import { DbAuthType } from './type';
import {
  alterPassRole,
  createDatabase,
  createRdsIamLoginRole,
  createUserPassLoginRole,
  grantRdsIamRole,
  listDatabase,
  listRdsIamRole,
  listRole,
  revokeRdsIamRole,
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
    console.info('result: ', result);

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
    convertToIamRole: [],
    newUserPassRole: [],
    convertToUserPassRole: [],
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

  const rdsIamRole = await listRdsIamRole(pgClient);

  // iterate for each microservice name configured
  for (const m of microserviceConfig) {
    // upsert role based on the configuration file
    if (m.authType == DbAuthType.USERNAME_PASSWORD) {
      const pass = await getMicroservicePassword(m.name);

      if (!roleList.includes(m.name)) {
        // crete role if it does not exist

        await createUserPassLoginRole(pgClient, m.name, pass);
        result.newUserPassRole.push(m.name);
      } else if (rdsIamRole.includes(m.name)) {
        // convert rdsIam role to username-password role

        await revokeRdsIamRole(pgClient, m.name);
        await alterPassRole(pgClient, m.name, pass);

        result.convertToUserPassRole.push(m.name);
      }
    } else if (m.authType == DbAuthType.RDS_IAM) {
      if (!roleList.includes(m.name)) {
        // crete role if it does not exist
        await createRdsIamLoginRole(pgClient, m.name);

        result.newIamRole.push(m.name);
      } else if (!rdsIamRole.includes(m.name)) {
        // grant rds_iam to the role if it has not been granted

        await grantRdsIamRole(pgClient, m.name);
        result.convertToIamRole.push(m.name);
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
