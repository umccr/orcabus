# Filemanager

The filemanager ingests events from cloud storage like S3 and maintains a queryable table of objects.

# Quickstart

For development edit/compile looping:

```
$ cargo install cargo-watch     # if not installed previously
$ cargo watch -c -w src -x run

   Compiling rust-api v0.1.0 (/Users/rvalls/dev/umccr/orcabus/skel/rust-api)
    Finished dev [unoptimized + debuginfo] target(s) in 1.74s
     Running `target/debug/rust-api`
2023-06-13T00:56:41.621002Z  INFO filemanager: listening on 0.0.0.0:8080
```

## Development

For localstack testing and development:

```sh
docker compose up
```

Then deploy the cdk to localstack:

```sh
cd deploy
npx cdklocal bootstrap
npx cdklocal deploy
```

Which allows creating events that are ingested:

```sh
awslocal s3api put-object --bucket filemanager-test-ingest --key test

/bin/bash aws-get-filemanager-logs.sh -c awslocal > logs.txt
```

### Database

Handy shortcut for database interaction, check `docs/developer/RUST_API.md` for more detailed ops:

```bash
docker exec -it orcabus_db mysql -h 0.0.0.0 -D orcabus -u root -proot
```