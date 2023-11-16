# Quickstart

First and foremost, make sure you setup a `.env` file from the `.env.example` and tilt up the database server, otherwise this skel will fail to compile:

```
error: `DATABASE_URL` must be set
```

For development edit/compile looping `cargo watch` helps:

```
$ cargo install cargo-watch     # if not installed previously
$ cargo watch -c -w src -x run

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
