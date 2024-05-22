#!/bin/sh
# Taken and adapted from: https://docs.aws.amazon.com/AmazonS3/latest/userguide/batch-ops-create-job.html

aws s3control create-job \
    --region ap-southeast-2 \
    --account-id acct-id \
    --operation '{"S3LambdaInvoke: ... args "}' \
    --manifest '{"Spec":{"Format":"S3BatchOperations_CSV_20180820","Fields":["Bucket","Key"]},"Location":{"ObjectArn":"arn:aws:s3:::umccr-temp-dev/manifest.csv"}}' \
    --report '{"Bucket":"arn:aws:s3::umccr-temp-dev","Prefix":"s3-batch-reports", "Format":"Report_CSV_20180820","Enabled":true,"ReportScope":"AllTasks"}' \
    --priority 42 \
    --role-arn S3-Batch-role \
    --client-request-token $(uuidgen) \
    --description "ICAv1 Batch Copy Job" \
    --no-confirmation-required
