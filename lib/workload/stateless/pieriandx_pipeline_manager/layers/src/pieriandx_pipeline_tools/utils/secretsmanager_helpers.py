#!/usr/bin/env python

import typing
from copy import copy
from typing import Dict
import boto3
from time import sleep
from os import environ
import json

if typing.TYPE_CHECKING:
    from mypy_boto3_secretsmanager import SecretsManagerClient
    from mypy_boto3_secretsmanager.type_defs import GetSecretValueResponseTypeDef

ICAV2_BASE_URL = "https://ica.illumina.com/ica/rest"


def get_secrets_manager_client() -> 'SecretsManagerClient':
    return boto3.client('secretsmanager')


def get_secret_value_from_aws_secrets_manager(secret_id: str) -> str:
    client = get_secrets_manager_client()

    secret_value_obj: GetSecretValueResponseTypeDef = client.get_secret_value(SecretId=secret_id)

    return secret_value_obj['SecretString']


def get_pieriandx_auth_token() -> str:
    from .lambda_helpers import run_lambda_function
    collection_token_lambda = environ.get("PIERIANDX_COLLECT_AUTH_TOKEN_LAMBDA_NAME")

    auth_token = run_lambda_function(collection_token_lambda, "")

    while auth_token is None or auth_token == 'null' or json.loads(auth_token).get("auth_token") is None:
        sleep(5)
        auth_token = run_lambda_function(collection_token_lambda, "")

    return json.loads(auth_token).get("auth_token")


def get_pieriandx_s3_access_credentials() -> Dict:
    secret_id = environ.get("PIERIANDX_S3_ACCESS_CREDENTIALS_SECRET_ID")

    access_credentials = get_secret_value_from_aws_secrets_manager(secret_id)

    access_credentials_dict = json.loads(access_credentials)

    for key in copy(access_credentials_dict).keys():
        access_credentials_dict[key.replace("s3", "aws").upper()] = access_credentials_dict.pop(key)

    return access_credentials_dict


def set_pieriandx_env_vars():
    environ["PIERIANDX_USER_AUTH_TOKEN"] = get_pieriandx_auth_token()


def set_icav2_env_vars():
    """
    Set the icav2 environment variables
    :return:
    """
    environ["ICAV2_BASE_URL"] = ICAV2_BASE_URL
    environ["ICAV2_ACCESS_TOKEN"] = get_secret_value_from_aws_secrets_manager(
        environ["ICAV2_ACCESS_TOKEN_SECRET_ID"]
    )


