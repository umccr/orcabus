#!/usr/bin/env python3

"""
Tools to handle secrets manager in AWS
"""

import typing
import boto3
import logging

if typing.TYPE_CHECKING:
    from mypy_boto3_secretsmanager import (SecretsManagerClient)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_secrets_manager_client() -> 'SecretsManagerClient':
    return boto3.client('secretsmanager')


def get_secret_string(secret_id: str) -> str:
    client: SecretsManagerClient = get_secrets_manager_client()

    response = client.get_secret_value(SecretId=str(secret_id))

    return response['SecretString']
