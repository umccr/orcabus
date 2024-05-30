#!/bin/sh
# Taken and adapted from: https://docs.aws.amazon.com/AmazonS3/latest/userguide/batch-ops-create-job.html

aws s3control create-job \
    --region ap-southeast-2 \
    --account-id 843407916570 \
    --operation '{"LambdaInvoke": {"FunctionArn": "arn:aws:lambda:ap-southeast-2:843407916570:function:OrcaBusBeta-ICAv1CopyBatc-ICAv1CopyBatchUtilitylam-6JWX9N3pNISt", "InvocationSchemaVersion": "2.0"}}' \
    --manifest '{"Spec":{"Format":"S3BatchOperations_CSV_20180820","Fields":["Bucket","Key"]},"Location":{"ObjectArn":"arn:aws:s3:::umccr-temp-dev/s3_batch_manifest.csv", "ETag": "05c846b0bc772e9637d50ddec5d65d6f"}}' \
    --report '{"Bucket":"arn:aws:s3:::umccr-temp-dev","Prefix":"s3-batch-reports", "Format":"Report_CSV_20180820","Enabled":true,"ReportScope":"AllTasks"}' \
    --priority 10 \
    --role-arn "arn:aws:iam::843407916570:role/OrcaBusBeta-ICAv1CopyBatc-S3BatchOperationsRole79F4-2sPLViRS0eKG" \
    --client-request-token $(uuidgen) \
    --description "ICAv1 Batch Copy Job" \
    --no-confirmation-required
