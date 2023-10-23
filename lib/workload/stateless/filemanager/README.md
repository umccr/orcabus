# Filemanager

The filemanager ingests events from cloud storage like S3 and maintains a queryable table of objects.

This project is split up into multiple crates in a workspace. For development, docker is used, which enables
localstack and a postgres database.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Rust](https://www.rust-lang.org/tools/install)
- [npm](https://www.npmjs.com/get-npm)
- [awslocal](https://github.com/localstack/awscli-local)

## Rust code development

Start the postgres database and ensure that an `.env` file is set containing the `DATABASE_URL`, e.g. see [`.env.example`][env-example]:

```sh
docker compose up
```

The filemanager uses sqlx to check if queries succeed against a database at compile time.
A `.env` file ensures that the sqlx code can check queries at compile time by providing a `DATABASE_URL`.

Filemanager uses docker to run a postgres database to track objects. This means that sqlx connects to the postgres server
running inside the docker compose container. If there are additional postgres installations locally (outside of docker),
this might interfere and complain about non-existing roles and users.

For development of the rust workspace, build manually:

```sh
cargo build --all-targets --all-features
```

Or watch and automatically recompile changes:

```sh
cargo install cargo-watch     # if not installed previously
cargo watch -c
```

Test with:

```sh
cargo test --all-targets
```

Formatting and clippy:

```sh
cargo clippy --all-targets
cargo fmt
```

[env-example]: .env.example

## Localstack development

Localstack enables deploying and testing AWS services locally. See the [deploy][deploy] directory
for the cdk infrastructure code.

For localstack testing and development:

```sh
docker compose up
```

Then deploy the cdk to localstack:

```sh
cd deploy

npm install

npx cdklocal bootstrap
npx cdklocal deploy
```

**WARNING**: it's possible that a profile called "default" in `~/.aws/config` could interfere with awslocal.

This allows creating events that are ingested.

First, push an object (in order to create a log group):
```sh
awslocal s3api put-object --bucket filemanager-test-ingest --key test
```

Then in a separate terminal:
```sh
./aws-get-filemanager-logs.sh -c awslocal
```

[deploy]: ./deploy

## Database

A shortcut for connecting to the docker database:

```bash
docker exec -it filemanager_db psql filemanager -U filemanager
```