# RDS Postgres Manager

This will deploy lambdas that will connect to the RDS instance with the master credential. This microservice is
responsible for admin Postgres activity that requires superuser access.

You would need to configure this service by passing it as props from the stack level
(`./config/stacks/postgresManager.ts`).

The config should register the microservice name and the connection type to the RDS. The connection can
make use of `rds_iam` or the conventional `user-password` connection string.

The microservice config should look as follows:

```ts
    microserviceDbConfig: [
      {
        name: 'metadata_manager',
        authType: DbAuthType.USERNAME_PASSWORD,
      },
      { 
        name: 'filemanager', 
        authType: DbAuthType.RDS_IAM 
      },
    ]
```

The DbAuthType is defined at the [./function/utils.ts](./function/utils.ts) in this project and it is as follows:

```ts
export enum DbAuthType {
  RDS_IAM,
  USERNAME_PASSWORD,
}
```

Once the configuration has been added, the stack will create the relevant new database and roles specified. The SQL
command is executed to the Db with AWS Custom Resource where the lambda is triggered on resource update.

Changing the microservice config will also execute changes to the role by updating the cloud formation stack props. E.g.
the `metadata_manager` is set to `user-pass` connection and a new configuration where it changes to use
`rds_iam`, the changes will update the login details in the database.

NOTE: When deleting a configuration from the props, it will NOT delete/drop any roles or database in the cluster.
