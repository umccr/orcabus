#!/usr/bin/env python3

"""

"""

import boto3
from pathlib import Path
import typing

from boto3.s3.transfer import S3Transfer

if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client


def get_s3_client(
        aws_access_key_id: str,
        aws_secret_access_key: str,
        aws_session_token: str
) -> 'S3Client':
    return boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token
    )


def upload_file_to_s3(
    local_path: Path,
    access_key_id: str,
    secret_access_key: str,
    session_token: str,
    bucket_name: str,
    key_prefix: str
):
    # Create an S3 client
    s3_client: S3Client = get_s3_client(
        access_key_id,
        secret_access_key,
        session_token
    )

    # Transfer file with upload
    transfer = S3Transfer(s3_client)

    transfer.upload_file(
        filename=local_path,
        bucket=bucket_name,
        key=key_prefix,
        extra_args={'ServerSideEncryption': "AES256"}
    )
