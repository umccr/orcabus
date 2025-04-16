#!/usr/bin/env python3

# Standard imports
import typing
from urllib.parse import urlunparse

import boto3
import json
from os import environ
import urllib3
from typing import Optional

http = urllib3.PoolManager()

LOCAL_HTTP_CACHE_PORT = 2773
PARAMETER_URL = '/systemsmanager/parameters/get/'
SECRETS_URL = '/secretsmanager/get/'

# Type hinting
if typing.TYPE_CHECKING:
    from mypy_boto3_secretsmanager import SecretsManagerClient
    from mypy_boto3_ssm import SSMClient


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


def get_orcabus_token() -> str:
    """
    From the AWS Secrets Manager, retrieve the OrcaBus token.
    :return:
    """
    return json.loads(get_secret_value(environ.get("ORCABUS_TOKEN_SECRET_ID")))['id_token']


def get_hostname() -> str:
    return get_ssm_value(environ.get("HOSTNAME_SSM_PARAMETER"))
