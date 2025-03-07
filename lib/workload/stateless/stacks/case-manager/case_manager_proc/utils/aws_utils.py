#!/usr/bin/env python3

# Standard imports
import typing
import boto3
import json
from os import environ

if typing.TYPE_CHECKING:
    from mypy_boto3_secretsmanager import SecretsManagerClient
    from mypy_boto3_ssm import SSMClient

ORCABUS_TOKEN_SECRET_ID = environ.get("ORCABUS_TOKEN_SECRET_ID")

sm_client: 'SecretsManagerClient' = boto3.client('secretsmanager')
ssm_client: 'SSMClient' = boto3.client('ssm')


def get_secretsmanager_client() -> 'SecretsManagerClient':
    return sm_client


def get_ssm_client() -> 'SSMClient':
    return ssm_client


def get_secret_value(secret_id: str) -> str:
    get_secret_value_response = get_secretsmanager_client().get_secret_value(SecretId=secret_id)
    return get_secret_value_response['SecretString']


def get_ssm_value(parameter_name: str) -> str:
    get_ssm_parameter_response = get_ssm_client().get_parameter(Name=parameter_name)
    return get_ssm_parameter_response['Parameter']['Value']


def get_orcabus_token() -> str:
    """
    From the AWS Secrets Manager, retrieve the OrcaBus token.
    (The ORCABUS_TOKEN_SECRET_ID env variable needs to be set to define the secret ID to fetch the token from)
    """
    return json.loads(get_secret_value(ORCABUS_TOKEN_SECRET_ID))['id_token']
