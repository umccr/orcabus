#!/usr/bin/env python3

"""
SSM parameter helpers
"""

# Imports
import boto3
import typing
from os import environ

# Globals
ICAV2_BASE_URL = "https://ica.illumina.com/ica/rest"
ICAV2_ACCESS_TOKEN_URN_SSM_PATH = "/icav2/umccr-prod/service-user-trial-jwt-token-secret-arn"
PIPELINE_ID_SSM_PARAMETER_PATH = "/icav2/umccr-prod/bclconvert_interop_qc_pipeline_id"


if typing.TYPE_CHECKING:
    from mypy_boto3_ssm.client import SSMClient
    from mypy_boto3_secretsmanager.client import SecretsManagerClient


# AWS things
def get_ssm_client() -> 'SSMClient':
    """
    Return SSM client
    """
    return boto3.client("ssm")


def get_secrets_manager_client() -> 'SecretsManagerClient':
    """
    Return Secrets Manager client
    """
    return boto3.client("secretsmanager")


def get_ssm_parameter_value(parameter_path) -> str:
    """
    Get the ssm parameter value from the parameter path
    :param parameter_path:
    :return:
    """
    return get_ssm_client().get_parameter(Name=parameter_path)["Parameter"]["Value"]


def get_secret(secret_id: str) -> str:
    """
    Return secret value
    """
    return get_secrets_manager_client().get_secret_value(SecretId=secret_id)["SecretString"]


# Set the icav2 environment variables
def set_icav2_env_vars():
    """
    Set the icav2 environment variables
    :return:
    """
    environ["ICAV2_BASE_URL"] = ICAV2_BASE_URL
    environ["ICAV2_ACCESS_TOKEN"] = get_secret(
        environ["ICAV2_ACCESS_TOKEN_SECRET_ID"]
    )


def get_interop_qc_pipeline_id_from_ssm() -> str:
    """

    Collect the Pipeline ID for the bclconvert interop qc path

    Returns:

    """
    return get_ssm_parameter_value(PIPELINE_ID_SSM_PARAMETER_PATH)
