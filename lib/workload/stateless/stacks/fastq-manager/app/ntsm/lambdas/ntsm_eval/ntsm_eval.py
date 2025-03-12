#!/usr/bin/env python3

"""
Evaluate the ntsm for two files
"""
from pathlib import Path
from subprocess import run
import typing
import boto3
from urllib.parse import urlparse
from typing import Tuple
from tempfile import NamedTemporaryFile

if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client


def get_s3_client() -> 'S3Client':
    """
    Get the s3 client
    :return:
    """
    return boto3.client('s3')


def get_bucket_key_from_uri(s3_uri: str) -> Tuple[str, str]:
    s3_obj = urlparse(s3_uri)

    return s3_obj.netloc, s3_obj.path


def download_s3_file_to_tmp(s3_client: 'S3Client', s3_uri: str) -> Path:
    """
    Download a file from s3 to a temporary file
    :param s3_client:
    :param s3_uri:
    :param tmp_file_path:
    :return:
    """
    bucket, key = get_bucket_key_from_uri(s3_uri)

    with NamedTemporaryFile(delete=False) as tmp_file:
        s3_client.download_fileobj(bucket, key, tmp_file)
        tmp_file_path = Path(tmp_file.name)

    return tmp_file_path


def handler(event, context):
    """
    Collect the two ntsm files
    :param event:
    :param context:
    :return:
    """
    s3 = get_s3_client()
    s3_uri_a = event['ntsmS3UriA']
    s3_uri_b = event['ntsmS3UriB']

    # Download the files
    ntsm_file_a = download_s3_file_to_tmp(s3, s3_uri_a)
    ntsm_file_b = download_s3_file_to_tmp(s3, s3_uri_b)

    # Evaluate the files
    run(['ntsmEval', "--all", ntsm_file_a, ntsm_file_b])

    # FIXME - no idea how to interact with the output yet
    return {
        "relatedness": 0.5,
    }