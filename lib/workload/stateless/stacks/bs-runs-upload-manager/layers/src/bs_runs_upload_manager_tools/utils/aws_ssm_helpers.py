#!/usr/bin/env python3

"""
Tools to handle secrets manager in AWS
"""

import typing
import boto3
import logging

if typing.TYPE_CHECKING:
    from mypy_boto3_ssm import SSMClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_ssm_client() -> 'SSMClient':
    return boto3.client('ssm')


def get_ssm_parameter_value(parameter_name: str) -> str:
    client: SSMClient = get_ssm_client()

    response = client.get_parameter(Name=parameter_name)

    return response['Parameter']['Value']
