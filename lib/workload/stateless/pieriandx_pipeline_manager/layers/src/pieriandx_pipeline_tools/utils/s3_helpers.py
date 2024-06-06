#!/usr/bin/env python

"""
Download file from s3
"""

import typing
from pathlib import Path

import boto3
from os import environ

if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client


def get_s3_client() -> 'S3Client':
    return boto3.client(
        's3',
        aws_access_key_id=environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=environ['AWS_SECRET_ACCESS_KEY']
    )


def upload_file(bucket: str, key: str, input_file_path: Path) -> None:
    s3 = get_s3_client()
    s3.upload_file(str(input_file_path), bucket, key.lstrip("/"))


def set_s3_access_cred_env_vars():
    from .secretsmanager_helpers import get_pieriandx_s3_access_credentials
    access_creds = get_pieriandx_s3_access_credentials()

    for key, value in access_creds.items():
        environ[key] = value
