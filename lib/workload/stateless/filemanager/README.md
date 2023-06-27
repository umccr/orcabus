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

Then:

```
$ curl localhost:8080/file/moo.bam
```

And to access the builtin Swagger playground, visit http://localhost:8080/swagger-ui/ on your browser.

## Development

For local(stack) testing and development:

```sh
pip install awscli-local
```

That allows one to interact with the S3 bucket events like so:

```sh
$ ./lib/workload/stateless/filemanager/localstack-s3-events-to-sqs.sh # Setup up the whole S3-SQS event registering
$ export AWS_REGION=ap-southeast-2
$ awslocal sqs list-queues
{
    "QueueUrls": [
        "http://localhost:4566/000000000000/filemanager_s3_events"
    ]
}
$ awslocal s3 cp ~/tmp/xilinx.jed s3://filemanager/
upload: ../../../tmp/xilinx.jed to s3://filemanager/xilinx.jed

% awslocal sqs receive-message --queue-url=http://localhost:4566/000000000000/filemanager_s3_events
{
    "Messages": [
        {
            "MessageId": "b4c9f3d9-b8aa-4193-958c-fa724ae77b50",
            "ReceiptHandle": "YWVmMWI3OWUtNTk2Ni00NmYwLTljODYtN2YyNWRhZWE5OWFiIGFybjphd3M6c3FzOmFwLXNvdXRoZWFzdC0yOjAwMDAwMDAwMDAwMDpmaWxlbWFuYWdlcl9zM19ldmVudHMgYjRjOWYzZDktYjhhYS00MTkzLTk1OGMtZmE3MjRhZTc3YjUwIDE2ODc3NDMyMTYuNTk0MjUwMg==",
            "MD5OfBody": "4dba243e4db081027122f9597a0422f7",
            "Body": "{\"Records\": [{\"eventVersion\": \"2.1\", \"eventSource\": \"aws:s3\", \"awsRegion\": \"ap-southeast-2\", \"eventTime\": \"2023-06-26T01:33:28.384Z\", \"eventName\": \"ObjectCreated:Put\", \"userIdentity\": {\"principalId\": \"AIDAJDPLRKLG7UEXAMPLE\"}, \"requestParameters\": {\"sourceIPAddress\": \"127.0.0.1\"}, \"responseElements\": {\"x-amz-request-id\": \"0df21e3c\", \"x-amz-id-2\": \"eftixk72aD6Ap51TnqcoF8eFidJG9Z/2\"}, \"s3\": {\"s3SchemaVersion\": \"1.0\", \"configurationId\": \"8ff04f8b-eb23-445c-af74-f350ffbf9b6c\", \"bucket\": {\"name\": \"filemanager\", \"ownerIdentity\": {\"principalId\": \"A3NL1KOZZKExample\"}, \"arn\": \"arn:aws:s3:::filemanager\"}, \"object\": {\"key\": \"lolo\", \"size\": 230764, \"eTag\": \"\\\"6548a5cd43a78152c559d81f37488786\\\"\", \"versionId\": null, \"sequencer\": \"0055AED6DCD90281E5\"}}}]}"
        }
    ]
}
```

### Database

Handy shortcut for database interaction, check `docs/developer/RUST_API.md` for more detailed ops:

```bash
docker exec -it orcabus_db mysql -h 0.0.0.0 -D orcabus -u root -proot
```