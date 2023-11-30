# Filemanager

The filemanager ingests events from cloud storage like S3 and maintains a queryable table of objects.

This project is split up into multiple crates in a workspace. For development, docker is used, which enables localstack and a postgres database.

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

A `.env` file ensures that the sqlx code can check queries at compile time by providing a `DATABASE_URL`. If `.env` is not present and there's no active database running and ready to be connected to, this project will fail to compile at all (preventing unnecessary runtime errors).

Filemanager uses docker to run a postgres database to track objects. This means that sqlx connects to the postgres server
running inside the docker compose container. If there are additional postgres installations locally (outside of docker),
this might interfere and complain about non-existing roles and users.

For development of the rust workspace, install a build cache (sccache) and build manually:

```sh
brew install sccache && export RUSTC_WRAPPER=`which sccache`
cargo build --all-targets --all-features
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

## Local development

Localstack enables deploying and testing AWS services locally. See the [deploy][deploy] directory
for the cdk infrastructure code.

In a nutshell, a filemanager developer only needs to run the following:

```sh
cargo install cargo-watch     # if not installed previously
cargo watch -- ./scripts/deploy.sh
```
To automatically recompile changes and re-deploy the changes.

Please don't use `scripts/deploy.sh` on production deployments, it is only meant for local development.

## Database

A shortcut for connecting to the docker database and inspecting its contents:

```bash
docker exec -it filemanager_db psql filemanager -U filemanager
```

Alternatively, just `brew install dbeaver-community` to easily browse the database contents.

[deploy]: ./deploy
[env-example]: .env.example