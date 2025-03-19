#!/usr/bin/env python3

# Standard imports
import typing
from typing import Optional
import boto3
import json
from os import environ
from urllib.parse import urlparse


# Type hinting
if typing.TYPE_CHECKING:
    from mypy_boto3_secretsmanager import SecretsManagerClient
    from mypy_boto3_ssm import SSMClient

ORCABUS_TOKEN_STR: Optional[str] = None
HOSTNAME_STR: Optional[str] = None


def get_secretsmanager_client() -> 'SecretsManagerClient':
    return boto3.client('secretsmanager')


def get_ssm_client() -> 'SSMClient':
    return boto3.client('ssm')


def get_secret_value(secret_id) -> str:
    """
    Collect the secret value
    :param secret_id:
    :return:
    """
    # Get the boto3 response
    get_secret_value_response = get_secretsmanager_client().get_secret_value(SecretId=secret_id)

    return get_secret_value_response['SecretString']


def get_ssm_value(parameter_name) -> str:
    # Get the boto3 response
    get_ssm_parameter_response = get_ssm_client().get_parameter(Name=parameter_name)

    return get_ssm_parameter_response['Parameter']['Value']


def set_orcabus_token():
    global ORCABUS_TOKEN_STR

    ORCABUS_TOKEN_STR = (
        json.loads(
            get_secret_value(environ.get("ORCABUS_TOKEN_SECRET_ID"))
        )['id_token']
    )


def get_orcabus_token() -> str:
    """
    From the AWS Secrets Manager, retrieve the OrcaBus token.
    :return:
    """
    if ORCABUS_TOKEN_STR is None:
        set_orcabus_token()
    return ORCABUS_TOKEN_STR


def set_hostname():
    global HOSTNAME_STR

    HOSTNAME_STR = get_ssm_value(environ.get("HOSTNAME_SSM_PARAMETER"))

def get_hostname() -> str:
    if HOSTNAME_STR is None:
        set_hostname()
    return HOSTNAME_STR


def get_bucket_key_pair_from_uri(s3_uri: str) -> (str, str):
    """
    Get the bucket and key from an s3 uri
    :param s3_uri:
    :return:
    """
    url_obj = urlparse(s3_uri)

    s3_bucket = url_obj.netloc
    s3_key = url_obj.path.lstrip('/')

    if s3_bucket is None or s3_key is None:
        raise ValueError(f"Invalid S3 URI: {s3_uri}")

    return s3_bucket, s3_key
