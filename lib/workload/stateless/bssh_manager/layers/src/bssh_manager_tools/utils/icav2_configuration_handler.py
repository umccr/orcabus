#!/usr/bin/env python

"""
Configuration handler

Get ICAv2 configuration handler
"""

import boto3

from mypy_boto3_ssm import SSMClient
from mypy_boto3_secretsmanager import SecretsManagerClient


from os import environ
from typing import Optional
from libica.openapi.v2 import Configuration
from .globals import ICAV2_BASE_URL, ICAV2_ACCESS_TOKEN_URN_SSM_PATH

# Global runtime vars
ICAV2_CONFIGURATION: Optional[Configuration] = None


# AWS things
def get_ssm_client() -> SSMClient:
    """
    Return SSM client
    """
    return boto3.client("ssm")


def get_secrets_manager_client() -> SecretsManagerClient:
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


def get_secret(secret_arn: str) -> str:
    """
    Return secret value
    """
    return get_secrets_manager_client().get_secret_value(SecretId=secret_arn)["SecretString"]


# Set the icav2 environment variables
def set_icav2_env_vars():
    """
    Set the icav2 environment variables
    :return:
    """
    environ["ICAV2_BASE_URL"] = ICAV2_BASE_URL
    environ["ICAV2_ACCESS_TOKEN"] = get_secret(
        get_ssm_parameter_value(ICAV2_ACCESS_TOKEN_URN_SSM_PATH)
    )


# ICAv2 Things
def get_icav2_base_url() -> str:
    """
    Return icav2 base url
    """
    return environ["ICAV2_BASE_URL"]


def get_icav2_access_token():
    """
    Return icav2 access token
    """
    return environ["ICAV2_ACCESS_TOKEN"]


def set_icav2_configuration():
    global ICAV2_CONFIGURATION
    ICAV2_CONFIGURATION = Configuration(
        host=get_icav2_base_url(),
        access_token=get_icav2_access_token()
    )


def get_icav2_configuration() -> Configuration:
    """
    Return icav2 configuration, if not set, sets it first, then returns
    :return:
    """
    if ICAV2_CONFIGURATION is None:
        set_icav2_configuration()
    return ICAV2_CONFIGURATION
