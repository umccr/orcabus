#!/usr/bin/env python3

# Standard imports
import typing
import boto3
import json
from os import environ


# Type hinting
if typing.TYPE_CHECKING:
    from mypy_boto3_secretsmanager import SecretsManagerClient
    from mypy_boto3_ssm import SSMClient


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


def get_orcabus_token() -> str:
    """
    From the AWS Secrets Manager, retrieve the OrcaBus token.
    :return:
    """
    return json.loads(get_secret_value(environ.get("ORCABUS_TOKEN_SECRET_ID")))['id_token']


def get_hostname() -> str:
    return get_ssm_value(environ.get("HOSTNAME_SSM_PARAMETER"))
