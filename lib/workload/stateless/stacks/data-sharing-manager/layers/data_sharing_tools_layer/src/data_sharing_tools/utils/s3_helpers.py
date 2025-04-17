#!/usr/bin/env python3

"""
Intro:

Given a list of json files, convert them into a single csv file and return as a string
"""

# Imports
import typing
import json
import boto3
from typing import List, Optional, Any, Dict
from tempfile import TemporaryDirectory
from pathlib import Path

# Set mypy type hinting
if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_s3.type_defs import ObjectTypeDef

# Set logging
import logging

logger = logging.getLogger()
logger.setLevel("INFO")


def get_s3_client() -> 'S3Client':
    return boto3.client('s3')


def download_s3_file(s3_client: 'S3Client', bucket: str, key: str, file_path: Path):
    # Create parent directory
    file_path.parent.mkdir(parents=True, exist_ok=True)
    # Download the file
    s3_client.download_file(Bucket=bucket, Key=key, Filename=str(file_path))


def list_s3_objects(s3_client: 'S3Client', bucket: str, prefix: str) -> List['ObjectTypeDef']:
    return s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)['Contents']


def download_all_s3_objects(s3_client: 'S3Client', bucket: str, prefix: str) -> Path:
    logging.info(f"Downloading all files in s3://{bucket}/{prefix}")
    with TemporaryDirectory(delete=False) as temp_dir:
        for s3_object in list_s3_objects(s3_client, bucket, prefix):
            file_path = Path(temp_dir).joinpath(Path(s3_object['Key']).relative_to(prefix))
            download_s3_file(s3_client, bucket, s3_object['Key'], file_path)
        return Path(temp_dir)


def read_in_json_objects_in_dir(dir_path: Path) -> List[Dict[str, Any]]:
    return list(map(
        lambda file_path: json.load(file_path, lines=True),
        dir_path.glob('*.json')
    ))


def read_in_s3_json_objects_as_list(bucket: str, prefix: str, s3_client: Optional['S3Client'] = None):
    if s3_client is None:
        s3_client = get_s3_client()

    local_data_path = download_all_s3_objects(s3_client, bucket, prefix)

    return read_in_json_objects_in_dir(local_data_path)


def upload_file_to_s3(s3_client: 'S3Client', file_path: Path, bucket: str, key: str):
    s3_client.upload_file(Filename=str(file_path), Bucket=bucket, Key=key)


def upload_obj_to_s3(data: Any, bucket: str, key: str, s3_client: Optional['S3Client'] = None):
    if s3_client is None:
        s3_client = get_s3_client()
    with TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir).joinpath('data.json')
        with open(file_path, 'w') as f_h:
            f_h.write(json.dumps(data))
        upload_file_to_s3(s3_client, file_path, bucket, key)


def upload_str_to_s3(data: str, bucket: str, key: str, s3_client: Optional['S3Client'] = None):
    if s3_client is None:
        s3_client = get_s3_client()
    with TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir).joinpath('data.csv')
        with open(file_path, 'w') as f_h:
            f_h.write(data)
        upload_file_to_s3(s3_client, file_path, bucket, key)


def delete_s3_obj(bucket: str, key: str, s3_client: Optional['S3Client'] = None):
    if s3_client is None:
        s3_client = get_s3_client()
    s3_client.delete_object(Bucket=bucket, Key=key)


def generate_presigned_url(bucket: str, key: str, expiration: Optional[int] = 604800, s3_client: Optional['S3Client'] = None):
    if s3_client is None:
        s3_client = get_s3_client()
    return s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': key},
        ExpiresIn=expiration
    )

