# Metadata Manager

One of the microservices in the OrcaBus that handles all the metadata information.

The metadata manager uses the Django framework.

## API

The API is deployed using a custom domain of `metadata` followed by the hosted name of the respective account
(`.dev.umccr.org`, `stg.umccr.org`). The hosted name can be retrieved from the SSM Parameter Store at
`/hosted_zone/umccr/name` from each account.
An example of the API endpoint is `https://metadata.umccr.org`.

The endpoint needs an authentication token which could be retrieved from the [token service
stack](../../../stateful/stacks/token-service/README.md). An example of retrieval is as follows.

```sh
export ORCABUS_TOKEN=$(aws secretsmanager get-secret-value --secret-id orcabus/token-service-jwt --output json --query SecretString | jq -r 'fromjson | .id_token')
```

The API currently supports the following paths:

- https://metadata.[STAGE].umccr.org/library
- https://metadata.[STAGE].umccr.org/specimen
- https://metadata.[STAGE].umccr.org/subject

Stage means the environment where the API is deployed, it could be `dev`, `stg`, or `prod` (or omit this for prod).

An example of how to use a curl command to access the production API:

```sh
curl -s -H "Authorization: Bearer $ORCABUS_TOKEN" "https://metadata.umccr.org/library" | jq
```

Filtering of results is also supported by the API. For example, to filter by `internal_id`, append the query parameter
to the URL: `.../library?internal_id=LIB001`

## Schema

This is the current (WIP) schema that reflects the current implementation.

![schema](docs/schema.drawio.svg)

To modify the diagram, open the `docs/schema.drawio.svg` with [diagrams.net](https://app.diagrams.net/?src=about).

## How things work

### How Syncing The Data Works

In the near future, we might introduce different ways to load data into the application. For the time being, we are
loading data
from the Google tracking sheet and mapping it to its respective model as follows.

| Sheet Header | Table      | Field Name |
|--------------|------------|------------|
| SubjectID    | `Subject`  | internalId |
| SampleID     | `Specimen` | internalId |
| Source       | `Specimen` | source     |
| LibraryID    | `Library`  | internalId |
| Phenotype    | `Library`  | phenotype  |
| Workflow     | `Library`  | workflow   |
| Quality      | `Library`  | quality    |
| Type         | `Library`  | type       |
| Coverage (X) | `Library`  | coverage   |
| Assay        | `Library`  | assay      |

Some important notes of the sync:

1. The sync will only run from the current year.
2. The tracking sheet is the single source of truth, any deletion/update on any record (including the record that has
   been
   loaded) will also apply to the existing data.
3. `LibraryId` is treated as a unique value in the tracking sheet, so for any duplicated value (including from other
   tabs) it will only recognize the last appearance.
4. In cases where multiple records share the same unique identifier (such as SampleId), only the data from the most
   recent record is stored. For instance, if a SampleId appears twice with differing source values, only the values from
   the latter record will be retained.
5. The sync happens every night periodically. See `./deploy/README.md` for more info.

Please refer to the [traking-sheet-service](proc/service/tracking_sheet_srv.py) implementation.

### Audit Data

The application is configured with [django-simple-history](https://django-simple-history.readthedocs.io/en/latest/)
so that each update to a particular record will have an audit trail. This extension will create an additional table
one-to-one with the original table with `historical` prefixing of the table name. The historical table will have
additional attributes that would indicate addition/update/deletion.

## Running Locally

Requirement:

- Python
- Docker

```bash
docker -v
Docker version 20.10.12, build e91ed5707e

python3 --version
Python 3.12.2
```

You would need to go to this microservice app directory from the root project

```bash
cd lib/workload/stateless/stacks/metadata-manager
```

### Setup

You would need to set up the Python environment (conda or venv)

```bash
conda create -n orcabus_mm python=3.12
conda activate orcabus_mm
```

or with venv as an alternative

```bash
python3 -mvenv .venv
source .venv/bin/activate
```

Before starting the app we need to install the dependencies

```bash
make install
```

### Load Data

To load existing data to the database, you could use the following command

```bash
make insert-data
```

If you have UMCCR dev credential, you could copy a psql dump file in the s3 bucket and restore it to the local database.

```bash
make s3-load
````

### Start

To start the application run the start command. This will run the server at `http://localhost:8000/`

```bash
make start
```

To insert some mock data to be inserted, run the following command while the server is running.

```bash
make insert-data
```

If you want a shortcut the combination of starting the server with loaded s3 data, you could use the following command.

```bash
make loaded-start
```

### Stop

To stop the running server, simply use the `make stop` command

### Testing

To run the test from scratch use `make test`, but if you want to test with a running database you could use `make suite`
.

### Development

#### Migrations

From time to time the model of the app will need to change and apply the migrations. The following command will create
the migration changes and apply the migration respectively.

```bash
make makemigrations
make migrate
```

#### SQL Queries

To quickly run raw sql queries to the database, `make psql` will log in to the psql server.

### Deployment

View the deployment docs [here](./deploy/README.md).
