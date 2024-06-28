# Large scale S3 file copy

This is a CDK stack and constructs to deploy a [highly scalable S3 file copy with S3 Batch Operations that can handle individual filesizes beyond 5GB][s3_batch_ops_greater_than_5GB] (up to >1TB, TBC).

This approach contrasts with pre-existing solutions such as [`rclone`][rclone] in not requiring any EC2-based infrastructure or additional AWS services (nor Fargate, Batch, Step Functions, etc...). If successful (faster and cheaper), this work could unlock more efficient data sharing scenarios (within AWS).

On the other hand, this is experimental and subject to heavy change since FinOps need to be balanced on this approach, as in answering the following question:

> When does S3 Batch Operations become more cost effective than alternative solutions?

Furthermore, at the time of writing this documentation, this microservice is meant to copy ICAv1 GDS storage towards a S3 bucket, which will introduce Illumina-specific logic. If this solution proves useful, further refactoring towards reusable constructs will follow.

## Deploy

From the deploy directory:

```
cdk deploy
```

Or from the top-level OrcaBus directory:

```
yarn cdk-stateless synth OrcaBusStatelessPipeline/OrcaBusBeta/ICAv1CopyBatchUtilityStack
```

## Invoke (manually)

```sh
aws lambda invoke --function-name OrcaBusBeta-ICAv1CopyBatc-ICAv1CopyBatchUtilitylam-1CjnVrJ26tzJ --cli-binary-format raw-in-base64-out --payload '{"RCLONE_SYNC_CONTENT_SOURCE": "src:stratus-gds-aps2/1f412e89-acc8-4337-b484-08d89d4636a9/Coverage_chk/SBJ03034/_manifest.json", "RCLONE_SYNC_CONTENT_DESTINATION": "dest:umccr-temp-dev/rclone-lambda-test/_manifest.json" }' response.json
```

[rclone]: https://rclone.org/
[s3_batch_ops_greater_than_5GB]: https://aws.amazon.com/blogs/storage/copying-objects-greater-than-5-gb-with-amazon-s3-batch-operations/
