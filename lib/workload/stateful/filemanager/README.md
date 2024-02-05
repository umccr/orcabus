# Filemanager

The filemanager ingests events from cloud storage like S3 and maintains a queryable table of objects.

This project is split up into multiple crates in a workspace. For development, docker is used, which enables a postgres database, the rest of the stack is developed against an AWS account.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Rust](https://www.rust-lang.org/tools/install)
- [npm](https://www.npmjs.com/get-npm)

## Rust code development

Start the postgres database and ensure that an `.env` file is set containing the `DATABASE_URL`, e.g. see [`.env.example`][env-example]:

```sh
docker compose up
```

The filemanager uses sqlx to check if queries succeed against a database at compile time.

A `.env` file ensures that the sqlx code can check queries at compile time by providing a `DATABASE_URL`. If `.env` is not present and there's no active database running and ready to be connected to, this project will fail to compile at all (preventing unnecessary runtime errors).

Filemanager uses docker to run a postgres database to track objects. This means that sqlx connects to the postgres server
running inside the docker compose container. If there are additional postgres installations locally (outside of docker),
this might interfere and complain about non-existing roles and users.

### Tooling prerequisites, testing and building the code

For development of the rust workspace, it's recommended to install a build cache (sccache) to improve compilation speeds:

```sh
brew install sccache && export RUSTC_WRAPPER=`which sccache`
```

or 

```sh
cargo install sccache && export RUSTC_WRAPPER=`which sccache`
```

Then install build prerequisites to build:

```sh
cargo install cargo-watch sqlx-cli
cargo build --all-targets --all-features
```

## Local development

Unit tests can be run with:

```sh
cargo test --all-targets --all-features
```

See the [deploy][deploy] directory for the cdk infrastructure code.

In a nutshell, a filemanager developer only needs to run the following to automatically recompile changes and re-deploy the changes:

```sh
./scripts/watch.sh
```


Please don't use `scripts/deploy.sh` on production deployments, it is only meant for development.

Formatting and clippy should also be run before committing changes:

```sh
cargo clippy --all-targets --all-features
cargo fmt
```

Note, some tests can take a while to run so they are ignored by default. It is still useful to run these tests sometimes, 
especially if changing code related to them. To do so, run the ignored tests with the `--ignored` flag:

```sh
cargo test --all-targets --all-features -- --ignored
```

## Database

A shortcut for connecting to the docker database and inspecting its contents:

```bash
docker exec -it filemanager_db psql filemanager -U filemanager
```

Alternatively, just `brew install dbeaver-community` to easily browse the database contents (or any other DB viewer you prefer).

[deploy]: ./deploy
[env-example]: .env.example

## Project Layout

The project is divided into multiple crates that serve different functionality.

* [filemanager]: This is the bulk of the filemanager logic, and handles database connections and event processing.
* [filemanager-http-lambda]: This is a Lambda function which calls the SQS queue manually to ingest events.
* [filemanager-ingest-lambda]: This is a Lambda function which ingests events directly passed from an SQS queue.
* [deploy]: CDK deployment code.
* [database]: Database migration files and queries.

[filemanager]: filemanager
[filemanager-http-lambda]: filemanager-http-lambda
[filemanager-ingest-lambda]: filemanager-ingest-lambda
[deploy]: deploy
[database]: database
