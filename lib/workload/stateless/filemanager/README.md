# Quickstart

For development edit/compile looping:

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

## Development

For local(stack) development:

```sh
pip install awscli-local
```

That allows one to interact with the S3 bucket events like so:

```sh
awslocal sqs list-queues
{
    "QueueUrls": [
        "http://localhost:4566/000000000000/filemanager_s3_events"
    ]
}
awslocal s3 cp ~/tmp/xilinx.jed s3://filemanager/
aws --endpoint-url=http://localhost:4566/_aws/sqs/messages sqs receive-message \
  --queue-url=http://queue.localhost.localstack.cloud:4566/000000000000/filemanager_s3_events
```