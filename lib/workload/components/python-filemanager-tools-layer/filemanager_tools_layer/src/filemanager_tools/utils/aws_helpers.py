#!/usr/bin/env python3

# Standard imports
import typing
from typing import Optional
import boto3
import json
from os import environ
from urllib.parse import urlparse, urlunparse
import urllib3
from typing import Optional

# Type hinting
if typing.TYPE_CHECKING:
    from mypy_boto3_secretsmanager import SecretsManagerClient
    from mypy_boto3_ssm import SSMClient

# Globals for storing secrets and parameters in memory
ORCABUS_TOKEN_STR: Optional[str] = None
HOSTNAME_STR: Optional[str] = None

# Globals for cache
LOCAL_HTTP_CACHE_PORT = 2773
PARAMETER_URL = '/systemsmanager/parameters/get/'
SECRETS_URL = '/secretsmanager/get/'


# Type hinting
if typing.TYPE_CHECKING:
    from mypy_boto3_secretsmanager import SecretsManagerClient
    from mypy_boto3_ssm import SSMClient

# Set pool manager
http = urllib3.PoolManager()


def retrieve_extension_value(url, query):
    url = str(urlunparse((
        'http', f'localhost:{LOCAL_HTTP_CACHE_PORT}',
        url, None,
        "&".join(list(map(
            lambda kv: f"{kv[0]}={kv[1]}",
            query.items()
        ))), None
    )))
    headers = { "X-Aws-Parameters-Secrets-Token": environ.get('AWS_SESSION_TOKEN') }
    response = http.request("GET", url, headers=headers)
    response = json.loads(response.data)
    return response


def get_ssm_value_from_cache(parameter_name: str) -> Optional[str]:
    try:
        return retrieve_extension_value(
            PARAMETER_URL,
            {
                "name": parameter_name,
            }
        )['Parameter']['Value']
    except Exception as e:
        return None


def get_secret_value_from_cache(secret_id: str) -> Optional[str]:
    try:
        return retrieve_extension_value(
            SECRETS_URL,
            {
                "secretId": secret_id,
            }
        )['SecretString']
    except Exception as e:
        return None


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
    secret_value_cached = get_secret_value_from_cache(secret_id)
    if secret_value_cached is not None:
        return secret_value_cached

    # Get the boto3 response
    get_secret_value_response = get_secretsmanager_client().get_secret_value(SecretId=secret_id)

    return get_secret_value_response['SecretString']


def get_ssm_value(parameter_name) -> str:
    """
    Collect the parameter from SSM
    :param parameter_name:
    :return:
    """
    ssm_parameter_cached = get_ssm_value_from_cache(parameter_name)
    if ssm_parameter_cached is not None:
        return ssm_parameter_cached

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
