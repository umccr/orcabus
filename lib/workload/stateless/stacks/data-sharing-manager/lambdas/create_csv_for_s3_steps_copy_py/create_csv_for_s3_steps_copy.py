#!/usr/bin/env python
import typing

import pandas as pd
from urllib.parse import urlparse
import boto3

if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_sts import STSClient


def get_s3_client() -> 'S3Client':
    return boto3.client("s3")


def get_sts_client() -> 'STSClient':
    return boto3.client("sts")


def handler(event, context):
    """
    Create csv for s3 steps copy
    :param event:
    :param context:
    :return:
    """

    # Create csv for steps copy and upload to s3
    source_uris_list = event.get("sourceUrisList")
    s3_steps_copy_bucket = event.get("s3StepsCopyBucket")
    s3_steps_copy_key = event.get("s3StepsCopyKey")

    # Ensure all inputs exist
    if not source_uris_list or not s3_steps_copy_bucket or not s3_steps_copy_key:
        raise ValueError("Missing required parameters: sourceUrisList, s3StepsCopyBucket, s3StepsCopyKey")

    # Generate dataframe
    s3_steps_copy_df = pd.DataFrame(
        list(map(
            lambda source_uri_iter_: {
                "bucket": urlparse(source_uri_iter_).netloc,
                "key": urlparse(source_uri_iter_).path.lstrip("/")
            },
            source_uris_list
        ))
    )

    # In development we have to add in 'a-working-folder/' as the prefix
    if get_sts_client().get_caller_identity()['Account'] == "843407916570":
        s3_steps_copy_key = 'a-working-folder/' + s3_steps_copy_key
        # Upload to s3
        # Upload to s3
        get_s3_client().put_object(
            Bucket=s3_steps_copy_bucket,
            Key=s3_steps_copy_key,
            Body=s3_steps_copy_df.to_json(orient='records').encode("utf-8"),
        )

    else:
        # Upload to s3
        get_s3_client().put_object(
            Bucket=s3_steps_copy_bucket,
            Key=s3_steps_copy_key,
            Body=s3_steps_copy_df.to_csv(index=False, header=False).encode("utf-8"),
        )
