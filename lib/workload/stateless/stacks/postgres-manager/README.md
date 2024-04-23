# RDS Postgres Manager

This will deploy lambdas that will connect to the RDS instance with the master credential. This microservice is
responsible for admin Postgres activity that requires superuser access.

Before using this microservice you would need to configure this lambda by passing it as props from stateless config
(`./config/constants.ts`) at the postgresManagerConfig.

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
