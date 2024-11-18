# Postgres data dump

Postgres data dump - a service that dumps (like `dd`) orcabus postgres databases to S3.

## Usage

Call the deployed function to update the current dump:

```sh
aws lambda invoke --function-name orcabus-pg-dd response.json
```

This is setup to dump the metadata_manager, workflow_manager, sequence_run_manager, and 10000 of the most recent
rows of the filemanager database.

## Configuration

This function can be configured by setting the following environment variables, see [.env.example][env-example] for an example:

| Name                                 | Description                                                                                                                                                                                                                             | Type                              |
|--------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------|
| `PG_DD_URL`                          | The database URL to dump databases from.                                                                                                                                                                                                | Postgres connection string        |
| `PG_DD_SECRET`                       | The secret name or ARN to fetch the database URL from. This is only used in the Lambda function, and overrides `PG_DD_URL`.                                                                                                             | `string`                          |
| `PG_DD_DATABASE_<DATABASE_NAME>`     | A name of the database to dump records from where `<DATABASE_NAME>` represents the target database. Specify this multiple times to use dump from multiple databases.                                                                    | `string`                          |
| `PG_DD_DATABASE_<DATABASE_NAME>_SQL` | Custom SQL code to execute when dumping database records for `<DATABASE_NAME>`. This is optional, and by default all records from all tables are dumped. Specify this is a list of SQL statements to generate a corresponding CSV file. | `string[]` or undefined           |
| `PG_DD_BUCKET`                       | The bucket to dump data to. This is required when deploying the Lambda function.                                                                                                                                                        | `string` or undefined             |
| `PG_DD_PREFIX`                       | The bucket prefix to use when writing to a bucket. This is optional.                                                                                                                                                                    | `string` or undefined             |
| `PG_DD_DIR`                          | The local filesystem directory to dump data to when running this command locally. This is not used on the deployed Lambda function.                                                                                                     | filesystem directory or undefined |

## Local development 

This project uses [poetry] to manage dependencies.

The pg-dd command can be run locally to dump data to a directory:

```
make local
```

Run the linter and formatter:

```
make check
```

[poetry]: https://python-poetry.org/
[env-example]: .env.example
