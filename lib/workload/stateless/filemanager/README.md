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
brew install sccache && export RUSTC_WRAPPER=`which sccache`
```

or

```sh
cargo install sccache && export RUSTC_WRAPPER=`which sccache`
```

Then, cargo-watch can be used to recompile files as they change:

```sh
cargo install cargo-watch sqlx-cli
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
especially if changing code related to them. To do so, run the ignored tests with the `--ignored` flag:

```sh
cargo test --all-targets --all-features -- --ignored
```

## Database

To connect to the local postgres database, run:

```bash
make psql
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
