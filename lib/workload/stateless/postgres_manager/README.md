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

There are 4 lambdas in this stack:

1. `orcabus-create-pg-db`

    This aimed to create a new database name for the microservice. The database name will be the same as the
    microservice name.

    ```sh
    aws lambda invoke \
      --function-name orcabus-create-pg-db \
      --payload '{ "microserviceName": "microservice_name" }' \
      --cli-binary-format raw-in-base64-out \
      response.json
    ```

2. `orcabus-create-pg-login-role`

    Create a role with login credentials used for this microservice.
    The name of the role would be the microservice name itself, and the credential will be saved into the secret
    manager. The secret manager name is saved to `orcabus/${microserviceName}/rdsLoginCredential`.

    Note: this will only work if the DbAuthType is configured to `USERNAME_PASSWORD`.

    ```sh
    aws lambda invoke \
      --function-name orcabus-create-pg-login-role \
      --payload '{ "microserviceName": "microservice_name" }' \
      --cli-binary-format raw-in-base64-out \
      response.json
    ```

3. `orcabus-create-pg-iam-role`

    Create a new role and assign `rds_iam` role to this role to be able to connect over IAM database authentication.

    A new managed policy will be created and the policy name
    will be `orcabus-rds-connect-${microservice_name}`. This could be attached to your compute role for access to the RDS and the token needed. Follow the documentation from AWS to connect to the RDS [here](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.Connecting.html).

    Note: this will only work if the microservice DbAuthType is configured to `RDS_IAM`.

    Ref:
    [aws-rds-iam-postgres](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.DBAccounts.html#UsingWithRDS.IAMDBAuth.DBAccounts.PostgreSQL)

    ```sh
    aws lambda invoke \
      --function-name orcabus-create-pg-iam-role \
      --payload '{ "microserviceName": "microservice_name" }' \
      --cli-binary-format raw-in-base64-out \
      response.json
    ```

4. `orcabus-alter-pg-db-owner`

    Alter existing db to its respective role. The respective role will be the microservice user role created in either
    lambda number 2 or 3.

    ```sh
    aws lambda invoke \
      --function-name orcabus-alter-pg-db-owner \
      --payload '{ "microserviceName": "microservice_name" }' \
      --cli-binary-format raw-in-base64-out \
      response.json
    ```
