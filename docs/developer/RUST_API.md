# Rust API Profile

- Use this profile if your microservice needs: ORM, API, LAMBDA, SQS

## App

- Consider building a microservice: `rust-api`

## Quickstart

Assuming you already have the Rust toolchain installed on your system, otherwise install it via:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

For development edit and compile loop, use the [`cargo-watch`](https://crates.io/crates/cargo-watch) crate:

```
$ cargo install cargo-watch     # if not installed previously
$ cargo watch -c -w src -x run  # Watches "src" dir, eXecutes "cargo run"

   Compiling rust-api v0.1.0 (/Users/rvalls/dev/umccr/orcabus/skel/rust-api)
    Finished dev [unoptimized + debuginfo] target(s) in 1.74s
     Running `target/debug/rust-api`
2023-06-13T00:56:41.621002Z  INFO rust_api: listening on 0.0.0.0:8080
```

Then:

```
$ curl localhost:8080/file/moo.bam
```

And to access the builtin Swagger playground, visit http://localhost:8080/swagger-ui/ on your browser.

# Database

Since this microservice is reliant on (meta)data present on the former "Data Portal" database, we'll have to load those tables in on the `orcabus_db` container and inner MySQL DB like so:

```bash
aws s3 cp s3://<data-portal-dev-bucket>/data_portal.sql.gz data/
docker cp data/data_portal.sql.gz orcabus_db:/
docker exec -i -e MYSQL_PWD=orcabus orcabus_db mysql -u orcabus -e "DROP DATABASE IF EXISTS orcabus; CREATE DATABASE IF NOT EXISTS orcabus;"
docker exec -i -e MYSQL_PWD=orcabus orcabus_db /bin/bash -c 'zcat data_portal.sql.gz | mysql -uorcabus orcabus'
```