# Filemanager

The filemanager ingests events from cloud storage like S3 and maintains a queryable table of objects.

This project is split up into multiple crates in a workspace. For development, docker is used, which enables a postgres database, the rest of the stack is developed against an AWS account.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Rust](https://www.rust-lang.org/tools/install)
- [npm](https://www.npmjs.com/get-npm)

## Rust code development

The filemanager uses docker to run a local postgres database to track objects, and sqlx, which connects to the database
at compile time to ensure that queries are valid. Compilation will emit errors if a query cannot successfully be run
on postgres database.

Makefile is used to simplify development. To get started run:

```sh
make build
```

This will spin up the docker postgres database, and compile the code using `cargo build`.

Note, that this sets an environment variable containing the `DATABASE_URL` to the local postgres database. This is variable
is expected by sqlx to check queries at compile time. If running `cargo` commands directly, this variable can be sourced
from an `.env` file. E.g. see [`.env.example`][env-example].

### Tooling pre-requisites, testing and building the code

For development of the rust workspace, it's recommended to install a build cache (sccache) to improve compilation speeds:

```sh
cargo install sccache && export RUSTC_WRAPPER=`which sccache`
```

cargo-watch can be used to recompile files as they change:

```sh
cargo install cargo-watch
make watch
```

## Linting and testing

Unit tests can be run with:

```sh
make test
```

Which runs `cargo test`.

To lint the code and format it, run:

```sh
make check-fix
```

This will run `cargo clippy` and `cargo fmt`.

Testing and linting should be run before committing changes to the repository.

See the [deploy][deploy] directory for the cdk infrastructure code.

Note, some tests can take a while to run so they are ignored by default. It is still useful to run these tests sometimes,
especially if changing code related to them. To do so, run the ignored tests with:

```sh
make test-ignored
```

Which runs `cargo test -- --ignored`.

## Database

To connect to the local postgres database, run:

```sh
make psql
```

Alternatively, just `brew install dbeaver-community` to easily browse the database contents (or any other DB viewer you prefer).

## Local API server

To use the local API server, run:

```sh
make api
```

### Compilation and migrations

Locally, database schemas are updated by passing migration scripts to the special `/docker-entrypoint-initdb.d/` directory
in the postgres [Dockerfile][dockerfile]. Locally, this is the most straight-forward solution as it doesn't require running
sqlx-cli to perform migrations. Note, this is different to deployed filemanager instances, which do use sqlx to perform
migrations.

It's possible that when updating the postgres schema files, compilation will fail because the currently running local
database is not up to date with the latest changes. By default, `make build` and other build-related commands will
rebuild the docker image, however sometimes it might be necessary to completely stop the container and prune the docker
system:

```sh
docker system prune -a --volumes
```

[dockerfile]: ./database/Dockerfile
[deploy]: ./deploy
[env-example]: .env.example

## Architecture

The filemanager ingest functionality operates to ensure eventual consistency in the database records. See the 
[ARCHITECTURE.md][architecture] for more details.

## Project Layout

The project is divided into multiple crates that serve different functionality.

* [filemanager]: This is the bulk of the filemanager logic, and handles database connections and event processing.
* [filemanager-api-lambda]: This is a Lambda function which responds to API Gateway requests.
* [filemanager-api-server]: A local server instance of the filemanager API.
* [filemanager-build]: Build related functionality such as database entity generation.
* [filemanager-ingest-lambda]: This is a Lambda function which ingests events directly passed from an SQS queue.
* [filemanager-inventory-lambda]: This function ingests events using [S3 Inventory][inventory].
* [filemanager-migrate-lambda]: A Lambda function to apply database migrations.
* [deploy]: CDK deployment code.
* [database]: Database migration files and queries.

[architecture]: docs/ARCHITECTURE.md
[filemanager]: filemanager
[filemanager-api-lambda]: filemanager-api-lambda
[filemanager-api-server]: filemanager-api-server
[filemanager-build]: filemanager-build
[filemanager-ingest-lambda]: filemanager-ingest-lambda
[filemanager-inventory-lambda]: filemanager-inventory-lambda
[filemanager-migrate-lambda]: filemanager-migrate-lambda
[inventory]: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-inventory.html
[deploy]: deploy
[database]: database
