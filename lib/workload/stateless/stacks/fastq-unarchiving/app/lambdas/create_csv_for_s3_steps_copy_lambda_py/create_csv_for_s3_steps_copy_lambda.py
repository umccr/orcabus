#!/usr/bin/env python3

"""
Create the csv for s3 copy steps,

Each row comprises the s3 bucket, s3 key

Using pandas is overkill but #wheninrome

We take an

"""

import typing
from typing import List, Dict, Tuple

from fastq_tools import get_fastq
from urllib.parse import urlparse
import pandas as pd
import boto3

# Type hinting
if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client


def get_s3_client() -> 'S3Client':
    return boto3.client('s3')


def upload_file_to_s3(bucket: str, key: str, file_contents: str):
    s3_client = get_s3_client()

    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=file_contents
    )


def get_s3_uris_from_fastq_id(fastq_id: str) -> List[str]:
    fastq_obj = get_fastq(fastq_id, includeS3Details=True)

    return list(filter(
        lambda s3_uri_iter_: s3_uri_iter_ is not None,
        [
            fastq_obj['readSet']['r1']['s3Uri'],
            fastq_obj['readSet'].get('r2', {}).get('s3Uri', None)
        ]
    ))


def split_s3_uri(s3_uri: str) -> Tuple[str, str]:
    s3_obj = urlparse(s3_uri)

    return s3_obj.netloc, s3_obj.path


def create_csv_for_s3_copy_steps(fastq_ids: List[str]) -> pd.DataFrame:
    """
    Create the csv for s3 copy steps,

    Each row comprises the s3 bucket, s3 key

    Using pandas is overkill but #wheninrome

    We take an
    :return:
    """
    rows = []

    for fastq_id in fastq_ids:
        # Get the s3 uris for each fastq id
        s3_uris = get_s3_uris_from_fastq_id(fastq_id)

        # For each s3 uri, split the s3 uris into bucket and key
        for s3_uri in s3_uris:
            bucket, key = split_s3_uri(s3_uri)

            rows.append({
                'bucket': bucket,
                'key': key
            })

    return pd.DataFrame(rows)


def handler(event, context):
    """
    Generate the csv for s3 copy steps
    :param event:
    :param context:
    :return:
    """
    fastq_ids = event['fastqIdList']
    steps_copy_bucket = event['s3StepsCopyBucket']
    steps_copy_key = event['s3StepsCopyKey']

    # Generate the csv
    copy_data_df = create_csv_for_s3_copy_steps(fastq_ids)

    # Uploading to s3
    upload_file_to_s3(
        steps_copy_bucket,
        steps_copy_key,
        copy_data_df.to_csv(header=False, index=False)
    )

